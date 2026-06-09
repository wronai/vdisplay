"""Persistent xdg-desktop-portal ScreenCast session (Etap 2 — one consent, many frames)."""

from __future__ import annotations

import os
import shutil
import subprocess
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
    active: bool = False
    source: str = "xdg-portal-screencast"

    @property
    def is_ready(self) -> bool:
        return self.active and bool(self.node_ids)

    def start(self, *, interactive: bool = True, timeout_s: float = 120.0) -> dict[str, Any]:
        payload = _start_screencast(interactive=interactive, timeout_s=timeout_s)
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
        self.active = True
        _set_active(self)
        return {
            "ok": True,
            "session_path": self.session_path,
            "node_ids": self.node_ids,
            "streams": self.streams,
            "source": self.source,
        }

    def status(self) -> dict[str, Any]:
        return {
            "active": self.active,
            "ready": self.is_ready,
            "session_path": self.session_path,
            "node_ids": self.node_ids,
            "streams": self.streams,
            "source": self.source,
        }

    def capture_png(self, *, node_index: int = 0) -> bytes:
        if not self.is_ready:
            raise VDisplayError("screencast session not ready — POST /session/screencast/start first")
        if node_index < 0 or node_index >= len(self.node_ids):
            raise VDisplayError(f"invalid screencast node_index {node_index}")
        return _capture_pipewire_node(self.node_ids[node_index])

    def stop(self) -> dict[str, Any]:
        was_active = self.active
        path = self.session_path
        self.active = False
        self.session_path = ""
        self.streams = []
        self.node_ids = []
        if _set_active_if_self(self):
            _set_active(None)
        if was_active and path:
            _close_screencast_session(path)
        return {"ok": True, "stopped": was_active, "session_path": path}


def _set_active_if_self(session: PortalScreenCastSession) -> bool:
    with _LOCK:
        return _ACTIVE is session


def start_screencast_session(*, interactive: bool = True, timeout_s: float = 120.0) -> PortalScreenCastSession:
    existing = get_active_screencast()
    if existing is not None and existing.is_ready:
        return existing
    if existing is not None:
        existing.stop()
    session = PortalScreenCastSession()
    session.start(interactive=interactive, timeout_s=timeout_s)
    return session


def stop_screencast_session() -> dict[str, Any]:
    session = get_active_screencast()
    if session is None:
        return {"ok": True, "stopped": False}
    return session.stop()


def _system_python() -> str:
    for candidate in ("/usr/bin/python3", shutil.which("python3")):
        if candidate and Path(candidate).is_file():
            return candidate
    return sys.executable


def _start_screencast(*, interactive: bool, timeout_s: float) -> dict[str, Any]:
    try:
        import dbus  # noqa: F401

        return _start_screencast_impl(interactive=interactive, timeout_s=timeout_s)
    except ImportError:
        return _start_screencast_subprocess(interactive=interactive, timeout_s=timeout_s)


def _start_screencast_impl(*, interactive: bool, timeout_s: float) -> dict[str, Any]:
    try:
        import dbus
        from dbus.mainloop.glib import DBusGMainLoop
        from gi.repository import GLib
    except ImportError as exc:
        return {"ok": False, "error": f"screencast needs python3-dbus and python3-gi: {exc}"}

    state: dict[str, Any] = {"ok": False, "stage": "create"}
    loop = GLib.MainLoop()

    def fail(error: str) -> None:
        state["ok"] = False
        state["error"] = error
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
        try:
            start_request = screencast.Start(state["session_path"], "", {})
            _listen_portal_request(bus, start_request, on_start)
        except Exception as exc:
            fail(f"screencast Start failed: {exc}")

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
        for item in streams:
            if isinstance(item, (list, tuple)) and item:
                node_id = int(item[0])
                node_ids.append(node_id)
                parsed_streams.append({"node_id": node_id, "properties": item[1] if len(item) > 1 else {}})
        if not node_ids:
            fail("screencast Start returned no pipewire streams")
            return
        state["streams"] = parsed_streams
        state["node_ids"] = node_ids
        state["ok"] = True
        loop.quit()

    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    proxy = bus.get_object("org.freedesktop.portal.Desktop", "/org/freedesktop/portal/desktop")
    screencast = dbus.Interface(proxy, dbus_interface="org.freedesktop.portal.ScreenCast")

    try:
        session_path = screencast.CreateSession({})
    except dbus.exceptions.DBusException as exc:
        return {"ok": False, "error": f"CreateSession failed: {exc}"}

    state["session_path"] = str(session_path)
    state["stage"] = "select"

    try:
        select_request = screencast.SelectSources(
            session_path,
            {
                "types": dbus.UInt32(1),
                "multiple": dbus.Boolean(False),
                "cursor_mode": dbus.UInt32(int(os.environ.get("VDISPLAY_SCREENCAST_CURSOR", "2"))),
                "interactive": dbus.Boolean(interactive),
            },
        )
        _listen_portal_request(bus, select_request, on_select)
    except dbus.exceptions.DBusException as exc:
        return {"ok": False, "error": f"SelectSources failed: {exc}"}

    GLib.timeout_add_seconds(max(1, int(timeout_s)), lambda: fail(f"screencast timed out after {timeout_s}s") or False)
    loop.run()

    if state.get("ok"):
        return {
            "ok": True,
            "session_path": state["session_path"],
            "streams": state.get("streams") or [],
            "node_ids": state.get("node_ids") or [],
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


def _capture_pipewire_node(node_id: int, *, timeout_s: float = 15.0) -> bytes:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        completed = subprocess.run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "pipewire",
                "-i",
                str(node_id),
                "-frames:v",
                "1",
                "-f",
                "image2pipe",
                "-vcodec",
                "png",
                "pipe:1",
            ],
            capture_output=True,
            timeout=timeout_s,
            check=False,
        )
        if completed.returncode == 0 and completed.stdout.startswith(b"\x89PNG"):
            return completed.stdout
        err = (completed.stderr or b"").decode("utf-8", errors="replace").strip()
        if err and "Unknown input format" not in err:
            raise VDisplayError(f"ffmpeg pipewire capture failed: {err}")

    gst = shutil.which("gst-launch-1.0")
    if gst:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            out = Path(tmp.name)
        try:
            completed = subprocess.run(
                [
                    gst,
                    "-e",
                    "pipewiresrc",
                    f"path={node_id}",
                    "!",
                    "videoconvert",
                    "!",
                    "pngenc",
                    "!",
                    "filesink",
                    f"location={out}",
                ],
                capture_output=True,
                timeout=timeout_s,
                check=False,
            )
            if completed.returncode == 0 and out.is_file() and out.stat().st_size > 64:
                return out.read_bytes()
            err = (completed.stderr or b"").decode("utf-8", errors="replace").strip()
            raise VDisplayError(f"gstreamer pipewire capture failed: {err or completed.returncode}")
        finally:
            out.unlink(missing_ok=True)

    raise VDisplayError(
        "pipewire frame capture needs ffmpeg built with pipewire support or gstreamer pipewiresrc"
    )


def _start_screencast_subprocess(*, interactive: bool, timeout_s: float) -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[3]
    src_path = repo_root / "src"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(src_path) + os.pathsep + env.get("PYTHONPATH", "")
    script = r'''
import json, sys
interactive = sys.argv[1].lower() in {"1", "true", "yes"}
timeout_s = float(sys.argv[2])
from vdisplay.capture.portal_screencast import _start_screencast_impl
print(json.dumps(_start_screencast_impl(interactive=interactive, timeout_s=timeout_s)))
'''
    system_py = _system_python()
    try:
        completed = subprocess.run(
            [system_py, "-c", script, str(interactive).lower(), str(timeout_s)],
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
