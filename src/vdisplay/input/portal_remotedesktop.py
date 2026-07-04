"""RemoteDesktop portal input — the sanctioned Wayland path for mouse+keyboard.

ydotool's absolute coordinate space proved opaque on multi-monitor HiDPI (the
cursor could land on the wrong monitor). The freedesktop RemoteDesktop portal,
linked to a ScreenCast stream, injects pointer motion in the STREAM's own
coordinate space — so a frame grabbed from that same stream shares one
coordinate system with the input. Proven end-to-end: text typed into a
right-docked IDE chat input (not the shell).

Flow:
    p = RemoteDesktopPortal().open()          # dialog once; restore token persists
    png = p.grab_frame()                      # a frame from the portal's stream
    sx, sy = p.frame_to_stream(fx, fy)        # scale frame px -> stream logical px
    p.move_abs(sx, sy); p.click(); p.type_text("hello"); p.submit()
    p.close()

Requires python-dbus + PyGObject (gi) + GStreamer with pipewiresrc — the same
stack the ScreenCast capture already uses. Run in an environment with those
(the vdisplay-agent's interpreter).
"""
from __future__ import annotations

import threading
from typing import Any

_BTN_LEFT = 272  # linux/input-event-codes BTN_LEFT
_KEYSYM_RETURN = 0xFF0D
_KEYSYM_BACKSPACE = 0xFF08
_KEYSYM_CONTROL_L = 0xFFE3


class RemoteDesktopError(RuntimeError):
    pass


class RemoteDesktopPortal:
    """A persistent RemoteDesktop+ScreenCast portal session for input injection.

    A private GLib main loop runs on a background thread to service async portal
    Request responses; public methods block until each step completes.
    """

    def __init__(self, *, restore_token: str | None = None, cursor_mode: int = 2) -> None:
        self._restore_token = restore_token
        self._cursor_mode = cursor_mode
        self._session: str | None = None
        self._node: int | None = None
        self._stream_size: tuple[int, int] = (0, 0)
        self._pw_fd: int | None = None
        self._new_restore_token: str | None = None
        self._loop = None
        self._thread: threading.Thread | None = None
        self._bus = None
        self._rd = None
        self._sc = None
        self._n = 0

    @staticmethod
    def _bootstrap_deps() -> None:
        # make system dbus/gi importable from any venv (same mechanism the
        # ScreenCast capture uses) so this works from e.g. koru's venv.
        try:
            from ..capture.portal_screencast import _ensure_portal_deps
            _ensure_portal_deps()
        except Exception:
            pass

    @staticmethod
    def available() -> tuple[bool, str]:
        RemoteDesktopPortal._bootstrap_deps()
        try:
            import dbus  # noqa: F401
            import gi
            gi.require_version("Gst", "1.0")
            from gi.repository import GLib, Gst  # noqa: F401
        except Exception as exc:  # pragma: no cover - env probe
            return False, f"portal deps unavailable ({exc})"
        return True, "RemoteDesktop portal input available"

    # ---- lifecycle -------------------------------------------------------
    def open(self, *, timeout_s: float = 60.0) -> "RemoteDesktopPortal":
        self._bootstrap_deps()
        import dbus
        from dbus.mainloop.glib import DBusGMainLoop
        from gi.repository import GLib

        DBusGMainLoop(set_as_default=True)
        self._bus = dbus.SessionBus()
        portal = self._bus.get_object("org.freedesktop.portal.Desktop", "/org/freedesktop/portal/desktop")
        self._rd = dbus.Interface(portal, "org.freedesktop.portal.RemoteDesktop")
        self._sc = dbus.Interface(portal, "org.freedesktop.portal.ScreenCast")
        self._loop = GLib.MainLoop()
        self._thread = threading.Thread(target=self._loop.run, daemon=True)
        self._thread.start()

        done = threading.Event()
        err: dict[str, Any] = {}
        GLib.idle_add(lambda: (self._begin(done, err) or False))
        if not done.wait(timeout_s):
            raise RemoteDesktopError("portal session setup timed out (approve the dialog?)")
        if err:
            raise RemoteDesktopError(err["msg"])
        return self

    def _tok(self, p: str) -> str:
        self._n += 1
        return f"{p}{self._n}"

    def _await(self, req: Any, cb) -> None:
        import dbus  # noqa: F401
        m: dict[str, Any] = {}

        def h(resp, res):
            self._bus.remove_signal_receiver(m["r"])
            cb(int(resp), res)
        m["r"] = self._bus.add_signal_receiver(
            h, signal_name="Response", dbus_interface="org.freedesktop.portal.Request", path=str(req))

    def _begin(self, done: threading.Event, err: dict[str, Any]) -> None:
        import dbus

        def fail(msg):
            err["msg"] = msg
            done.set()

        def sess(r, res):
            if r:
                return fail(f"CreateSession failed ({r})")
            self._session = res["session_handle"]
            self._await(self._rd.SelectDevices(self._session, {"handle_token": self._tok("h"), "types": dbus.UInt32(3)}), dev)

        def dev(r, res):
            if r:
                return fail(f"SelectDevices failed ({r})")
            opts = {"handle_token": self._tok("h"), "types": dbus.UInt32(1),
                    "multiple": False, "cursor_mode": dbus.UInt32(self._cursor_mode)}
            self._await(self._sc.SelectSources(self._session, opts), src)

        def src(r, res):
            if r:
                return fail(f"SelectSources failed ({r})")
            opts = {"handle_token": self._tok("h")}
            if self._restore_token:
                opts["restore_token"] = self._restore_token
                opts["persist_mode"] = dbus.UInt32(2)
            else:
                opts["persist_mode"] = dbus.UInt32(2)
            self._await(self._rd.Start(self._session, "", opts), start)

        def start(r, res):
            if r:
                return fail(f"Start denied ({r})")
            self._new_restore_token = res.get("restore_token")
            streams = res.get("streams", [])
            if not streams:
                return fail("no streams")
            nid, props = streams[0]
            self._node = int(nid)
            w, h = props.get("size", (0, 0))
            self._stream_size = (int(w), int(h))
            self._pw_fd = self._sc.OpenPipeWireRemote(self._session, {}).take()
            done.set()

        opts = {"handle_token": self._tok("h"), "session_handle_token": self._tok("s")}
        self._await(self._rd.CreateSession(opts), sess)

    @property
    def restore_token(self) -> str | None:
        return self._new_restore_token

    @property
    def stream_size(self) -> tuple[int, int]:
        return self._stream_size

    # ---- capture ---------------------------------------------------------
    def grab_frame(self, *, timeout_s: float = 5.0) -> bytes:
        """One PNG frame from the portal's own stream."""
        import gi
        gi.require_version("Gst", "1.0")
        from gi.repository import Gst
        Gst.init(None)
        import os
        import tempfile

        out = tempfile.NamedTemporaryFile(prefix="rdportal-", suffix=".png", delete=False)
        out.close()
        pipe = Gst.parse_launch(
            f"pipewiresrc fd={self._pw_fd} path={self._node} num-buffers=1 ! "
            f"videoconvert ! pngenc ! filesink location={out.name}")
        pipe.set_state(Gst.State.PLAYING)
        msg = pipe.get_bus().timed_pop_filtered(
            int(timeout_s) * Gst.SECOND, Gst.MessageType.EOS | Gst.MessageType.ERROR)
        pipe.set_state(Gst.State.NULL)
        if msg is not None and msg.type == Gst.MessageType.ERROR:
            raise RemoteDesktopError(f"frame grab failed: {msg.parse_error()}")
        try:
            with open(out.name, "rb") as fh:
                return fh.read()
        finally:
            try:
                os.remove(out.name)
            except OSError:
                pass

    def frame_to_stream(self, fx: float, fy: float, *, frame_w: int, frame_h: int) -> tuple[int, int]:
        """Scale a pixel in a grabbed frame to the stream's logical coord space.

        The frame buffer resolution (e.g. 2560x1600) can differ from the stream's
        declared logical size (e.g. 2048x1280); NotifyPointerMotionAbsolute wants
        the latter.
        """
        sw, sh = self._stream_size
        if not frame_w or not frame_h or not sw or not sh:
            return int(fx), int(fy)
        return int(fx * sw / frame_w), int(fy * sh / frame_h)

    # ---- input -----------------------------------------------------------
    def move_abs(self, x: int, y: int) -> None:
        self._rd.NotifyPointerMotionAbsolute(self._session, {}, self._u32(self._node), float(x), float(y))

    def click(self, button: int = _BTN_LEFT) -> None:
        self._rd.NotifyPointerButton(self._session, {}, self._i32(button), self._u32(1))
        self._rd.NotifyPointerButton(self._session, {}, self._i32(button), self._u32(0))

    def key(self, keysym: int) -> None:
        self._rd.NotifyKeyboardKeysym(self._session, {}, self._i32(keysym), self._u32(1))
        self._rd.NotifyKeyboardKeysym(self._session, {}, self._i32(keysym), self._u32(0))

    def type_text(self, text: str) -> None:
        for ch in text:
            self.key(ord(ch))  # ASCII keysym == char code for basic Latin

    def key_combo(self, modifier_keysym: int, keysym: int) -> None:
        """Press modifier, press+release key, release modifier (e.g. Ctrl+Enter)."""
        self._rd.NotifyKeyboardKeysym(self._session, {}, self._i32(modifier_keysym), self._u32(1))
        self._rd.NotifyKeyboardKeysym(self._session, {}, self._i32(keysym), self._u32(1))
        self._rd.NotifyKeyboardKeysym(self._session, {}, self._i32(keysym), self._u32(0))
        self._rd.NotifyKeyboardKeysym(self._session, {}, self._i32(modifier_keysym), self._u32(0))

    def submit(self, *, mode: str = "enter") -> None:
        """Send the chat message. mode='enter' (Return) or 'ctrl-enter' (Ctrl+Enter,
        which is how Qoder and several IDE chats submit)."""
        if mode == "ctrl-enter":
            self.key_combo(_KEYSYM_CONTROL_L, _KEYSYM_RETURN)
        else:
            self.key(_KEYSYM_RETURN)

    def click_focuses_input(self, sx: int, sy: int, *, verify) -> bool:
        """Move+click at stream (sx, sy), then confirm the click actually
        focused the intended input before any text is typed — so a drifted
        target can NEVER leak keystrokes into the wrong window (e.g. a shell).

        ``verify(before_png, after_png)`` returns True if the after-click frame
        shows the input focused (caller supplies the check — e.g. the input's
        focus ring appeared, or the placeholder region changed near the target).
        """
        import time

        before = self.grab_frame()
        self.move_abs(sx, sy)
        time.sleep(0.35)
        self.click()
        time.sleep(0.45)
        after = self.grab_frame()
        try:
            return bool(verify(before, after))
        except Exception:
            return False

    def type_into_input_verified(
        self, sx: int, sy: int, text: str, *, verify, submit: bool = False,
        clear_first: bool = False, clear_count: int = 200, submit_mode: str = "enter",
    ) -> bool:
        """Focus-guarded type: only types (and optionally submits) if the click
        is confirmed to have focused the input. ``clear_first`` empties the input
        (backspaces) before typing so pre-existing text doesn't accumulate.
        Returns whether it typed."""
        import time

        if not self.click_focuses_input(sx, sy, verify=verify):
            return False
        if clear_first:
            self.clear_input(clear_count)
            time.sleep(0.2)
        self.type_text(text)
        if submit:
            time.sleep(0.2)
            self.submit(mode=submit_mode)
        return True

    def clear_input(self, count: int = 64) -> None:
        for _ in range(count):
            self.key(_KEYSYM_BACKSPACE)

    def _u32(self, v: int):
        import dbus
        return dbus.UInt32(int(v))

    def _i32(self, v: int):
        import dbus
        return dbus.Int32(int(v))

    def close(self) -> None:
        try:
            if self._session is not None:
                self._rd.Close if False else None  # session closed with the bus
        finally:
            if self._loop is not None:
                self._loop.quit()
