"""Persistent xdg-desktop-portal ScreenCast session (Etap 2 — one consent, many frames)."""

from __future__ import annotations

import os
import fcntl
import shutil
import subprocess
import warnings
import sys
import tempfile
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..exceptions import VDisplayError

_ACTIVE: PortalScreenCastSession | None = None
_LOCK = threading.Lock()


def get_active_screencast() -> PortalScreenCastSession | None:
    with _LOCK:
        return _ACTIVE


def _set_active(session: PortalScreenCastSession | None) -> None:
    global _ACTIVE
    with _LOCK:
        _ACTIVE = session


@dataclass
class PortalScreenCastSession:
    """Hold an open portal ScreenCast session and grab PNG frames from PipeWire."""

    session_path: str = ""
    streams: list[dict[str, Any]] = field(default_factory=list)
    node_ids: list[int] = field(default_factory=list)
    stream_targets: list[str] = field(default_factory=list)
    pipewire_fd: int | None = None
    active: bool = False
    source: str = "xdg-portal-screencast"

    @property
    def is_ready(self) -> bool:
        return self.active and bool(self.node_ids) and bool(self.session_path)

    def start(
        self,
        *,
        interactive: bool = True,
        timeout_s: float = 120.0,
        multiple: bool | None = None,
    ) -> dict[str, Any]:
        payload = _start_screencast(interactive=interactive, timeout_s=timeout_s, multiple=multiple)
        if not payload.get("ok"):
            raise VDisplayError(str(payload.get("error") or "screencast start failed"))

        self.session_path = str(payload.get("session_path") or "")
        self.streams = list(payload.get("streams") or [])
        self.node_ids = [int(node) for node in payload.get("node_ids") or [] if str(node).isdigit()]
        if not self.node_ids and self.streams:
            for stream in self.streams:
                node = stream.get("node_id")
                if node is not None:
                    self.node_ids.append(int(node))
        self.stream_targets = [str(item) for item in payload.get("stream_targets") or []]
        if not self.stream_targets and self.streams:
            for stream in self.streams:
                self.stream_targets.append(_stream_target(int(stream["node_id"]), stream.get("properties") or {}))
        fd = payload.get("pipewire_fd")
        self.pipewire_fd = int(fd) if fd is not None else None
        self.active = True
        _set_active(self)
        return {
            "ok": True,
            "session_path": self.session_path,
            "node_ids": self.node_ids,
            "streams": self.streams,
            "source": self.source,
            "has_pipewire_fd": bool(self.session_path),
        }

    def status(self) -> dict[str, Any]:
        return {
            "active": self.active,
            "ready": self.is_ready,
            "session_path": self.session_path,
            "node_ids": self.node_ids,
            "streams": self.streams,
            "source": self.source,
            "has_pipewire_fd": bool(self.session_path),
        }

    def capture_png(self, *, node_index: int = 0) -> bytes:
        if not self.is_ready:
            raise VDisplayError("screencast session not ready — POST /session/screencast/start first")
        if node_index < 0 or node_index >= len(self.node_ids):
            raise VDisplayError(f"invalid screencast node_index {node_index}")
        serial = None
        if node_index < len(self.streams):
            serial = _stream_serial(self.streams[node_index].get("properties") or {})
        fd = _open_screencast_pipewire_fd(self.session_path)
        try:
            return _capture_pipewire_stream(
                pipewire_fd=fd,
                node_id=self.node_ids[node_index],
                target_object=serial,
            )
        finally:
            os.close(fd)

    def stop(self) -> dict[str, Any]:
        was_active = self.active
        path = self.session_path
        fd = self.pipewire_fd
        self.active = False
        self.session_path = ""
        self.streams = []
        self.node_ids = []
        self.stream_targets = []
        self.pipewire_fd = None
        if fd is not None:
            _close_pipewire_fd(fd)
        if _set_active_if_self(self):
            _set_active(None)
        if was_active and path:
            _close_screencast_session(path)
        return {"ok": True, "stopped": was_active, "session_path": path}


def _set_active_if_self(session: PortalScreenCastSession) -> bool:
    with _LOCK:
        return _ACTIVE is session


def _screencast_multiple(explicit: bool | None) -> bool:
    if explicit is not None:
        return explicit
    return os.environ.get("VDISPLAY_SCREENCAST_MULTIPLE", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def start_screencast_session(
    *,
    interactive: bool = True,
    timeout_s: float = 120.0,
    multiple: bool | None = None,
) -> PortalScreenCastSession:
    from .linux_xwd import is_blank_png

    existing = get_active_screencast()
    if existing is not None and existing.is_ready:
        try:
            probe = existing.capture_png()
            if not is_blank_png(probe):
                return existing
        except VDisplayError:
            pass
        invalidate_screencast_session(existing)
    elif existing is not None:
        invalidate_screencast_session(existing)
    session = PortalScreenCastSession()
    session.start(interactive=interactive, timeout_s=timeout_s, multiple=multiple)
    return session


def stop_screencast_session() -> dict[str, Any]:
    session = get_active_screencast()
    if session is None:
        return {"ok": True, "stopped": False}
    return session.stop()


def invalidate_screencast_session(session: PortalScreenCastSession | None) -> None:
    """Drop a stale ScreenCast session so the next start opens a fresh portal stream."""
    if session is None:
        _set_active(None)
        return
    try:
        session.stop()
    except VDisplayError:
        session.active = False
        session.session_path = ""
        session.node_ids = []
        session.streams = []
        session.stream_targets = []
        session.pipewire_fd = None
        if _set_active_if_self(session):
            _set_active(None)


def _system_python() -> str:
    for candidate in ("/usr/bin/python3", shutil.which("python3")):
        if candidate and Path(candidate).is_file():
            return candidate
    return sys.executable


def _ensure_portal_deps() -> None:
    """Allow portal capture from venv by picking up system python3-gi."""
    try:
        from gi.repository import GLib  # noqa: F401

        return
    except ImportError:
        pass
    for path in (
        "/usr/lib/python3/dist-packages",
        f"/usr/lib/python{sys.version_info.major}.{sys.version_info.minor}/dist-packages",
    ):
        if path not in sys.path and os.path.isdir(path):
            sys.path.append(path)


def _open_screencast_pipewire_fd(session_path: str) -> int:
    """Open a fresh PipeWire fd for an active portal ScreenCast session."""
    try:
        _ensure_portal_deps()
        import dbus
    except ImportError as exc:
        raise VDisplayError(f"screencast capture needs python3-dbus: {exc}") from exc

    bus = dbus.SessionBus()
    proxy = bus.get_object("org.freedesktop.portal.Desktop", "/org/freedesktop/portal/desktop")
    screencast = dbus.Interface(proxy, dbus_interface="org.freedesktop.portal.ScreenCast")
    fd = _dbus_fd(
        screencast.OpenPipeWireRemote(
            session_path,
            dbus.Dictionary({}, signature="sv"),
        )
    )
    if fd < 0:
        raise VDisplayError("OpenPipeWireRemote returned no fd")
    owned_fd = os.dup(fd)
    os.close(fd)
    _ensure_fd_inheritable(owned_fd)
    return owned_fd


def _start_screencast(
    *,
    interactive: bool,
    timeout_s: float,
    multiple: bool | None = None,
) -> dict[str, Any]:
    allow_multiple = _screencast_multiple(multiple)
    try:
        _ensure_portal_deps()
        import dbus  # noqa: F401
        from gi.repository import GLib  # noqa: F401

        return _start_screencast_impl(
            interactive=interactive,
            timeout_s=timeout_s,
            multiple=allow_multiple,
        )
    except ImportError:
        return _start_screencast_subprocess(
            interactive=interactive,
            timeout_s=timeout_s,
            multiple=allow_multiple,
        )


def _portal_request_path(bus, token: str) -> str:
    unique = bus.get_unique_name()[1:].replace(".", "_")
    return f"/org/freedesktop/portal/desktop/request/{unique}/{token}"


def _stream_properties(raw: Any) -> dict[str, Any]:
    if not raw:
        return {}
    return {str(key): value for key, value in dict(raw).items()}


def _stream_serial(properties: dict[str, Any]) -> str | None:
    serial = properties.get("pipewire-serial")
    if serial is not None:
        return str(int(serial))
    return None


def _stream_target(node_id: int, properties: dict[str, Any]) -> str:
    return _stream_serial(properties) or str(node_id)


def _ensure_fd_inheritable(fd: int) -> None:
    flags = fcntl.fcntl(fd, fcntl.F_GETFD)
    fcntl.fcntl(fd, fcntl.F_SETFD, flags & ~fcntl.FD_CLOEXEC)


def _dbus_fd(value: Any) -> int:
    if value is None:
        return -1
    if hasattr(value, "fileno"):
        fd = int(value.fileno())
    elif hasattr(value, "take"):
        fd = int(value.take())
    else:
        fd = int(value)
    if fd >= 0:
        _ensure_fd_inheritable(fd)
    return fd


def _close_pipewire_fd(fd: int) -> None:
    try:
        os.close(fd)
    except OSError:
        pass


def _start_screencast_impl(
    *,
    interactive: bool,
    timeout_s: float,
    multiple: bool = False,
) -> dict[str, Any]:
    try:
        import dbus
        from dbus.mainloop.glib import DBusGMainLoop
        from gi.repository import GLib
    except ImportError as exc:
        return {"ok": False, "error": f"screencast needs python3-dbus and python3-gi: {exc}"}

    state: dict[str, Any] = {"ok": False, "stage": "create", "session_path": ""}
    loop = GLib.MainLoop()
    token_counter = {"n": 0}

    def next_token(label: str) -> str:
        token_counter["n"] += 1
        return f"vdisplay_sc_{label}_{token_counter['n']}"

    def fail(error: str) -> None:
        state["ok"] = False
        state["error"] = error
        loop.quit()

    def on_start(response, results) -> None:
        code = int(response)
        if code != 0:
            if code == 1:
                fail("user cancelled screencast start")
            elif code == 2:
                fail("screencast start denied")
            else:
                fail(f"Start failed with response={code}")
            return
        streams = results.get("streams") or []
        parsed_streams: list[dict[str, Any]] = []
        node_ids: list[int] = []
        stream_targets: list[str] = []
        for item in streams:
            if isinstance(item, (list, tuple)) and item:
                node_id = int(item[0])
                properties = _stream_properties(item[1] if len(item) > 1 else {})
                node_ids.append(node_id)
                stream_targets.append(_stream_target(node_id, properties))
                parsed_streams.append({"node_id": node_id, "properties": properties})
        if not node_ids:
            fail("screencast Start returned no pipewire streams")
            return
        try:
            fd = _dbus_fd(
                screencast.OpenPipeWireRemote(
                    state["session_path"],
                    dbus.Dictionary({}, signature="sv"),
                )
            )
        except Exception as exc:
            fail(f"OpenPipeWireRemote failed: {exc}")
            return
        if fd < 0:
            fail("OpenPipeWireRemote returned no fd")
            return
        # Dup before the dbus/GLib loop exits — the portal fd is closed otherwise.
        owned_fd = os.dup(fd)
        os.close(fd)
        _ensure_fd_inheritable(owned_fd)
        state["streams"] = parsed_streams
        state["node_ids"] = node_ids
        state["stream_targets"] = stream_targets
        state["pipewire_fd"] = owned_fd
        state["ok"] = True
        loop.quit()

    def on_select(response, results) -> None:
        code = int(response)
        if code != 0:
            if code == 1:
                fail("user cancelled screencast source selection")
            elif code == 2:
                fail(
                    "screencast denied (Screen Recording permission missing). "
                    "GNOME: Settings → Privacy → Screen Recording → enable vdisplay-agent."
                )
            else:
                fail(f"SelectSources failed with response={code}")
            return
        state["stage"] = "start"
        start_token = next_token("start")
        start_path = _portal_request_path(bus, start_token)
        _listen_portal_request(bus, start_path, on_start)
        try:
            screencast.Start(
                state["session_path"],
                "",
                {"handle_token": start_token},
            )
        except Exception as exc:
            fail(f"screencast Start failed: {exc}")

    def on_create(response, results) -> None:
        code = int(response)
        if code != 0:
            if code == 1:
                fail("user cancelled screencast session creation")
            elif code == 2:
                fail("screencast session creation denied")
            else:
                fail(f"CreateSession failed with response={code}")
            return
        session_path = str(results.get("session_handle") or "")
        if not session_path:
            fail("CreateSession returned no session_handle")
            return
        state["session_path"] = session_path
        state["stage"] = "select"
        select_token = next_token("select")
        select_path = _portal_request_path(bus, select_token)
        _listen_portal_request(bus, select_path, on_select)
        try:
            screencast.SelectSources(
                session_path,
                {
                    "handle_token": select_token,
                    "types": dbus.UInt32(1),
                    "multiple": dbus.Boolean(multiple),
                    "cursor_mode": dbus.UInt32(int(os.environ.get("VDISPLAY_SCREENCAST_CURSOR", "2"))),
                    "interactive": dbus.Boolean(interactive),
                },
            )
        except Exception as exc:
            fail(f"SelectSources failed: {exc}")

    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    proxy = bus.get_object("org.freedesktop.portal.Desktop", "/org/freedesktop/portal/desktop")
    screencast = dbus.Interface(proxy, dbus_interface="org.freedesktop.portal.ScreenCast")

    create_token = next_token("create")
    create_path = _portal_request_path(bus, create_token)
    _listen_portal_request(bus, create_path, on_create)

    try:
        screencast.CreateSession(
            {
                "handle_token": create_token,
                "session_handle_token": "vdisplay_screencast",
            }
        )
    except dbus.exceptions.DBusException as exc:
        return {"ok": False, "error": f"CreateSession failed: {exc}"}

    GLib.timeout_add_seconds(max(1, int(timeout_s)), lambda: fail(f"screencast timed out after {timeout_s}s") or False)
    loop.run()

    if state.get("ok"):
        return {
            "ok": True,
            "session_path": state["session_path"],
            "streams": state.get("streams") or [],
            "node_ids": state.get("node_ids") or [],
            "stream_targets": state.get("stream_targets") or [],
            "pipewire_fd": state.get("pipewire_fd"),
        }
    return {"ok": False, "error": state.get("error") or "screencast failed"}


def _listen_portal_request(bus, request_path, callback) -> None:
    def on_response(response, results) -> None:
        callback(response, results)

    bus.add_signal_receiver(
        on_response,
        dbus_interface="org.freedesktop.portal.Request",
        signal_name="Response",
        path=str(request_path),
    )


def _close_screencast_session(session_path: str) -> None:
    try:
        import dbus

        bus = dbus.SessionBus()
        session = bus.get_object("org.freedesktop.portal.Desktop", session_path)
        iface = dbus.Interface(session, dbus_interface="org.freedesktop.portal.Session")
        iface.Close()
    except Exception:
        pass


def _capture_pipewire_stream(
    *,
    pipewire_fd: int,
    node_id: int,
    target_object: str | None = None,
    timeout_s: float = 30.0,
) -> bytes:
    cap_fd = os.dup(pipewire_fd)
    try:
        _ensure_fd_inheritable(cap_fd)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            out = Path(tmp.name)
        try:
            if _capture_pipewire_frame_gi_subprocess(
                cap_fd,
                node_id,
                target_object,
                out,
                timeout_s=timeout_s,
            ):
                return out.read_bytes()
            return _capture_pipewire_frame_gst_launch(
                cap_fd,
                node_id,
                target_object,
                out,
                timeout_s=timeout_s,
            )
        finally:
            out.unlink(missing_ok=True)
    finally:
        os.close(cap_fd)


_CAPTURE_FRAME_SCRIPT = r'''
import sys

fd = int(sys.argv[1])
node_id = int(sys.argv[2])
target = sys.argv[3]
out_path = sys.argv[4]
timeout_s = float(sys.argv[5])

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst

Gst.init(None)
props = f"fd={fd} always-copy=1 num-buffers=1"
if target:
    props += f" target-object={target}"
else:
    props += f" path={node_id}"
pipe = Gst.parse_launch(
    "pipewiresrc " + props
    + " ! queue max-size-buffers=1 max-size-time=0 max-size-bytes=0 leaky=downstream"
    + " ! videoconvert ! pngenc ! appsink name=sink sync=false max-buffers=1 drop=true"
)
sink = pipe.get_by_name("sink")
pipe.set_state(Gst.State.PLAYING)
sample = sink.emit("try-pull-sample", int(timeout_s * 1_000_000_000))
pipe.set_state(Gst.State.NULL)
if sample is None:
    raise SystemExit("pipewire capture timed out waiting for frame")
buf = sample.get_buffer()
ok, info = buf.map(Gst.MapFlags.READ)
if not ok:
    raise SystemExit("pipewire capture failed to map buffer")
try:
    data = bytes(info.data)
finally:
    buf.unmap(info)
if len(data) < 64:
    raise SystemExit("pipewire capture returned empty frame")
with open(out_path, "wb") as fh:
    fh.write(data)
'''


def _capture_pipewire_frame_gi_subprocess(
    cap_fd: int,
    node_id: int,
    target_object: str | None,
    out: Path,
    *,
    timeout_s: float,
) -> bool:
    system_py = _system_python()
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="pass_fds overriding close_fds", category=RuntimeWarning)
            completed = subprocess.run(
                [
                    system_py,
                    "-c",
                    _CAPTURE_FRAME_SCRIPT,
                    str(cap_fd),
                    str(node_id),
                    target_object or "",
                    str(out),
                    str(timeout_s),
                ],
                capture_output=True,
                text=True,
                timeout=timeout_s + 5.0,
                check=False,
                close_fds=False,
                pass_fds=tuple(sorted({0, 1, 2, cap_fd})),
            )
    except subprocess.TimeoutExpired:
        return False
    if completed.returncode == 0 and out.is_file() and out.stat().st_size > 64:
        return True
    return False


def _capture_pipewire_frame_gst_launch(
    cap_fd: int,
    node_id: int,
    target_object: str | None,
    out: Path,
    *,
    timeout_s: float,
) -> bytes:
    gst = shutil.which("gst-launch-1.0")
    if not gst:
        raise VDisplayError(
            "pipewire frame capture needs python3-gi+GStreamer or gstreamer pipewiresrc"
        )
    src_args = [
        "pipewiresrc",
        f"fd={cap_fd}",
        "always-copy=1",
        "num-buffers=1",
    ]
    if target_object:
        src_args.append(f"target-object={target_object}")
    else:
        src_args.append(f"path={node_id}")
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="pass_fds overriding close_fds", category=RuntimeWarning)
        completed = subprocess.run(
            [
                gst,
                "-e",
                *src_args,
                "!",
                "queue",
                "max-size-buffers=1",
                "max-size-time=0",
                "max-size-bytes=0",
                "leaky=downstream",
                "!",
                "videoconvert",
                "!",
                "pngenc",
                "!",
                "filesink",
                f"location={out}",
                "sync=false",
                "async=false",
            ],
            capture_output=True,
            timeout=timeout_s,
            check=False,
            close_fds=False,
            pass_fds=tuple(sorted({0, 1, 2, cap_fd})),
        )
    if completed.returncode == 0 and out.is_file() and out.stat().st_size > 64:
        return out.read_bytes()
    err = (completed.stderr or b"").decode("utf-8", errors="replace").strip()
    raise VDisplayError(f"gstreamer pipewire capture failed: {err or completed.returncode}")


def _capture_pipewire_node(node_id: int, *, timeout_s: float = 15.0) -> bytes:
    """Legacy helper for tests; portal capture requires OpenPipeWireRemote fd."""
    return _capture_pipewire_stream(pipewire_fd=-1, node_id=node_id, timeout_s=timeout_s)


def _vdisplay_src_path() -> Path:
    import vdisplay

    root = Path(vdisplay.__file__).resolve().parent
    return root.parent if root.name == "vdisplay" and (root.parent / "vdisplay").is_dir() else root


def _start_screencast_subprocess(
    *,
    interactive: bool,
    timeout_s: float,
    multiple: bool = False,
) -> dict[str, Any]:
    src_path = _vdisplay_src_path()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(src_path) + os.pathsep + env.get("PYTHONPATH", "")
    env.setdefault("VDISPLAY_AGENT_BROKER", "0")
    script = r'''
import json, sys
interactive = sys.argv[1].lower() in {"1", "true", "yes"}
timeout_s = float(sys.argv[2])
multiple = sys.argv[3].lower() in {"1", "true", "yes"}
from vdisplay.capture.portal_screencast import _start_screencast_impl
result = _start_screencast_impl(interactive=interactive, timeout_s=timeout_s, multiple=multiple)
if isinstance(result, dict) and result.get("pipewire_fd") is not None:
    result = dict(result)
    result.pop("pipewire_fd", None)
print(json.dumps(result))
'''
    system_py = _system_python()
    try:
        completed = subprocess.run(
            [system_py, "-c", script, str(interactive).lower(), str(timeout_s), str(multiple).lower()],
            capture_output=True,
            text=True,
            timeout=timeout_s + 10,
            check=False,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"screencast timed out after {timeout_s}s"}

    try:
        import json

        payload = json.loads((completed.stdout or "").strip() or "{}")
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        pass
    err = (completed.stderr or completed.stdout or "screencast subprocess failed").strip()
    return {"ok": False, "error": err}
