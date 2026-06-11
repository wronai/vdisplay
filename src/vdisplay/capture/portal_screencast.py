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
_KNOWN_SESSION_PATHS: set[str] = set()


def _remember_screencast_path(session_path: str) -> None:
    path = str(session_path or "").strip()
    if path:
        _KNOWN_SESSION_PATHS.add(path)


def _forget_screencast_path(session_path: str) -> None:
    path = str(session_path or "").strip()
    if path:
        _KNOWN_SESSION_PATHS.discard(path)


_RESTORE_TOKEN_FILE = Path(
    os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
) / "vdisplay-screencast-restore-token"


def _save_restore_token(token: str) -> None:
    """Persist the portal ScreenCast restore_token for dialog-free restarts."""
    try:
        _RESTORE_TOKEN_FILE.write_text(token.strip(), encoding="utf-8")
    except OSError:
        pass


def _load_restore_token() -> str | None:
    """Load a previously persisted restore_token, if available."""
    try:
        token = _RESTORE_TOKEN_FILE.read_text(encoding="utf-8").strip()
        return token if token else None
    except (OSError, ValueError):
        return None


def _purge_stale_screencast_sessions() -> None:
    for path in list(_KNOWN_SESSION_PATHS):
        _close_screencast_session(path)
        _KNOWN_SESSION_PATHS.discard(path)


def get_active_screencast() -> PortalScreenCastSession | None:
    with _LOCK:
        return _ACTIVE


def _set_active(session: PortalScreenCastSession | None) -> None:
    global _ACTIVE
    with _LOCK:
        _ACTIVE = session


def ensure_portal_session_env() -> dict[str, str]:
    """Fill missing GUI session vars so xdg-desktop-portal can show dialogs."""
    uid = os.getuid()
    runtime = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{uid}"
    updates: dict[str, str] = {}
    if not os.environ.get("XDG_RUNTIME_DIR") and os.path.isdir(runtime):
        updates["XDG_RUNTIME_DIR"] = runtime
    bus_path = f"{runtime}/bus"
    if not os.environ.get("DBUS_SESSION_BUS_ADDRESS") and os.path.exists(bus_path):
        updates["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={bus_path}"
    if not os.environ.get("WAYLAND_DISPLAY"):
        for name in ("wayland-1", "wayland-0"):
            if os.path.exists(f"{runtime}/{name}"):
                updates["WAYLAND_DISPLAY"] = name
                break
    if not os.environ.get("DISPLAY"):
        updates["DISPLAY"] = ":0"
    for key, value in updates.items():
        os.environ[key] = value
    return updates


def portal_session_env_status() -> tuple[bool, str]:
    """Return whether portal ScreenCast can reach the user's session bus."""
    ensure_portal_session_env()
    runtime = os.environ.get("XDG_RUNTIME_DIR", "")
    dbus_addr = os.environ.get("DBUS_SESSION_BUS_ADDRESS", "")
    if not dbus_addr:
        return (
            False,
            "DBUS_SESSION_BUS_ADDRESS is missing — start vdisplay-agent serve from a local "
            "GUI terminal (not SSH/Cursor sandbox), or export DBUS_SESSION_BUS_ADDRESS.",
        )
    bus_path = dbus_addr.removeprefix("unix:path=")
    if bus_path and not os.path.exists(bus_path):
        return (
            False,
            f"session bus not found at {bus_path} — run from your desktop session "
            f"(XDG_RUNTIME_DIR={runtime or 'unset'}).",
        )
    return True, ""


def _apply_keeper_fields(session, payload: dict[str, Any]) -> None:
    session.keeper_managed = bool(payload.get("keeper_managed"))
    session.keeper_socket_path = str(
        payload.get("socket_path") or payload.get("keeper_socket_path") or ""
    )
    session.keeper_runtime_dir = str(
        payload.get("runtime_dir") or payload.get("keeper_runtime_dir") or ""
    )
    try:
        session.keeper_pid = int(payload.get("keeper_pid") or payload.get("pid") or 0)
    except (TypeError, ValueError):
        session.keeper_pid = 0
    if session.keeper_socket_path and not session.keeper_managed:
        session.keeper_managed = True


def refresh_screencast_adopt_payload(session: PortalScreenCastSession, payload: dict[str, Any]) -> None:
    """Update an adopted session from a fresh keeper/adopt payload."""
    if payload.get("streams"):
        session.streams = list(payload.get("streams") or [])
    if payload.get("node_ids"):
        session.node_ids = [int(n) for n in payload.get("node_ids") or [] if str(n).isdigit()]
    elif session.streams and not session.node_ids:
        session.node_ids = session._parse_node_ids(payload)
    if payload.get("stream_targets"):
        session.stream_targets = [str(item) for item in payload.get("stream_targets") or []]
    elif session.streams and not session.stream_targets:
        session.stream_targets = session._parse_stream_targets(payload)
    session.active = True
    _apply_keeper_fields(session, payload)


def _probe_adopt_screencast_fd(session, session_path: str) -> bool:
    """Probe the fd for an adopted session.

    Returns True if the caller should return the session early (invalid
    session tolerated), False otherwise.
    """
    probe_fd: int | None = None
    try:
        if session.pipewire_fd is not None and session.pipewire_fd >= 0:
            probe_fd = os.dup(session.pipewire_fd)
        else:
            probe_fd = _open_screencast_pipewire_fd(session_path)
    except VDisplayError as exc:
        msg = str(exc).lower()
        if "invalid session" in msg or "access denied" in msg:
            session.pipewire_fd = None
            _set_active(session)
            return True
        raise VDisplayError(f"adopted screencast session not usable: {exc}") from exc
    finally:
        if probe_fd is not None and probe_fd >= 0:
            os.close(probe_fd)
    return False


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
    keeper_managed: bool = False
    keeper_socket_path: str = ""
    keeper_runtime_dir: str = ""
    keeper_pid: int = 0
    _portal_bus: Any = field(default=None, repr=False, compare=False)

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
        self.node_ids = self._parse_node_ids(payload)
        self.stream_targets = self._parse_stream_targets(payload)
        fd = payload.get("pipewire_fd")
        self.pipewire_fd = int(fd) if fd is not None else None
        self._portal_bus = payload.get("_portal_bus")
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

    @classmethod
    def from_portal_payload(
        cls,
        payload: dict[str, Any],
        *,
        verify_remote: bool = True,
    ) -> PortalScreenCastSession:
        """Adopt an existing portal ScreenCast session opened in another process."""
        ensure_portal_session_env()
        ok, hint = portal_session_env_status()
        if not ok:
            raise VDisplayError(hint)

        session_path = str(payload.get("session_path") or "").strip()
        if not session_path:
            raise VDisplayError("adopt screencast requires session_path")

        session = cls()
        session.session_path = session_path
        session.streams = list(payload.get("streams") or [])
        session.node_ids = [int(n) for n in payload.get("node_ids") or [] if str(n).isdigit()]
        session.stream_targets = [str(item) for item in payload.get("stream_targets") or []]
        if not session.node_ids:
            session.node_ids = session._parse_node_ids(payload)
        if not session.stream_targets:
            session.stream_targets = session._parse_stream_targets(payload)
        if not session.node_ids:
            raise VDisplayError("adopt screencast requires node_ids or streams")

        fd = payload.get("pipewire_fd")
        session.pipewire_fd = int(fd) if fd is not None else None
        session.active = True
        _apply_keeper_fields(session, payload)

        if verify_remote and _probe_adopt_screencast_fd(session, session_path):
            return session

        _set_active(session)
        return session

    def detach_local(self) -> None:
        """Stop tracking this session in-process without closing the portal session."""
        if _set_active_if_self(self):
            _set_active(None)

    def _parse_node_ids(self, payload: dict[str, Any]) -> list[int]:
        node_ids = [int(n) for n in payload.get("node_ids") or [] if str(n).isdigit()]
        if not node_ids and self.streams:
            for stream in self.streams:
                node = stream.get("node_id")
                if node is not None:
                    node_ids.append(int(node))
        return node_ids

    def _parse_stream_targets(self, payload: dict[str, Any]) -> list[str]:
        targets = [str(item) for item in payload.get("stream_targets") or []]
        if not targets and self.streams:
            for stream in self.streams:
                targets.append(_stream_target(int(stream["node_id"]), stream.get("properties") or {}))
        return targets

    def status(self) -> dict[str, Any]:
        return {
            "active": self.active,
            "ready": self.is_ready,
            "session_path": self.session_path,
            "node_ids": self.node_ids,
            "streams": self.streams,
            "source": self.source,
            "has_pipewire_fd": bool(self.session_path),
            "keeper_managed": self.keeper_managed,
            "keeper_socket_path": self.keeper_socket_path,
            "keeper_pid": self.keeper_pid or None,
        }

    def capture_png(self, *, node_index: int = 0) -> bytes:
        if not self.is_ready:
            raise VDisplayError("screencast session not ready — POST /session/screencast/start first")
        from .screencast_keeper import request_keeper_capture, session_uses_keeper

        if session_uses_keeper(self):
            try:
                return request_keeper_capture(
                    node_index=node_index,
                    session_path=self.session_path,
                    socket_path=self.keeper_socket_path or None,
                )
            except VDisplayError as exc:
                msg = str(exc).lower()
                if "socket unavailable" in msg or "no response" in msg:
                    raise VDisplayError(
                        f"{exc} — restart screencast keeper: vdisplay agent screencast start --force"
                    ) from exc
                raise
        return self.capture_png_local(node_index=node_index)

    def capture_png_local(
        self,
        *,
        node_index: int = 0,
        try_all_streams: bool = True,
    ) -> bytes:
        """Capture via PipeWire in this process (keeper daemon only)."""
        if not self.is_ready:
            raise VDisplayError("screencast session not ready — POST /session/screencast/start first")
        timeout_s = _pipewire_capture_timeout_s()
        errors: list[str] = []
        indices = [node_index]
        if try_all_streams:
            for index in range(len(self.node_ids)):
                if index not in indices:
                    indices.append(index)
        for index in indices:
            if index < 0 or index >= len(self.node_ids):
                continue
            properties: dict[str, Any] = {}
            if index < len(self.streams):
                properties = self.streams[index].get("properties") or {}
            portal_id = properties.get("id")
            fd: int | None = None
            try:
                fd = _screencast_pipewire_fd(self, fresh=False)
                return _capture_pipewire_stream(
                    pipewire_fd=fd,
                    node_id=self.node_ids[index],
                    target_object=_stream_serial(properties, node_id=self.node_ids[index]),
                    portal_stream_id=str(portal_id) if portal_id is not None else None,
                    stream_size=_stream_properties_size(properties),
                    timeout_s=timeout_s,
                )
            except VDisplayError as exc:
                errors.append(f"node[{index}]={self.node_ids[index]}: {exc}")
                if (
                    _gnome_screenshot_fallback_enabled()
                    and index == node_index
                ):
                    try:
                        return _capture_via_gnome_screenshot_region(properties)
                    except VDisplayError as fb_exc:
                        errors.append(
                            f"node[{index}]={self.node_ids[index]} gnome-screenshot: {fb_exc}"
                        )
            finally:
                if fd is not None:
                    os.close(fd)
                    fd = None
            if self.pipewire_fd is not None and _pipewire_fresh_fd_enabled():
                try:
                    fd = _screencast_pipewire_fd(self, fresh=True)
                    return _capture_pipewire_stream(
                        pipewire_fd=fd,
                        node_id=self.node_ids[index],
                        target_object=_stream_serial(properties, node_id=self.node_ids[index]),
                        portal_stream_id=str(portal_id) if portal_id is not None else None,
                        stream_size=_stream_properties_size(properties),
                        timeout_s=timeout_s,
                    )
                except VDisplayError as retry_exc:
                    errors.append(
                        f"node[{index}]={self.node_ids[index]} (fresh fd): {retry_exc}"
                    )
                finally:
                    if fd is not None:
                        os.close(fd)
        detail = "; ".join(errors) or "no pipewire nodes"
        raise VDisplayError(f"screencast frame capture failed ({detail})")

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
        self._portal_bus = None
        if fd is not None:
            _close_pipewire_fd(fd)
        if _set_active_if_self(self):
            _set_active(None)
        if path:
            _remember_screencast_path(path)
            _close_screencast_session(path)
            _forget_screencast_path(path)
        return {"ok": True, "stopped": bool(path) or was_active, "session_path": path}


def _set_active_if_self(session: PortalScreenCastSession) -> bool:
    with _LOCK:
        return _ACTIVE is session


def _screencast_multiple(explicit: bool | None) -> bool:
    if explicit is not None:
        return explicit
    disabled = os.environ.get("VDISPLAY_SCREENCAST_MULTIPLE", "").strip().lower()
    if disabled in {"0", "false", "no"}:
        return False
    # Default: request All Screens — required for multi-monitor web console.
    return True


def prepare_portal_screencast_start() -> None:
    """Close stale portal ScreenCast sessions before opening a new one."""
    stop_screencast_session()
    _purge_stale_screencast_sessions()


def screencast_adopt_payload(session: PortalScreenCastSession, **extra: Any) -> dict[str, Any]:
    """Serialize a portal session for POST /session/screencast/adopt."""
    payload: dict[str, Any] = {
        "session_path": session.session_path,
        "streams": session.streams,
        "node_ids": session.node_ids,
        "stream_targets": session.stream_targets,
    }
    if session.keeper_managed:
        payload["keeper_managed"] = True
    if session.keeper_socket_path:
        payload["socket_path"] = session.keeper_socket_path
    if session.keeper_runtime_dir:
        payload["runtime_dir"] = session.keeper_runtime_dir
    if session.keeper_pid:
        payload["keeper_pid"] = session.keeper_pid
    payload.update(extra)
    return payload


def start_screencast_session(
    *,
    interactive: bool = True,
    timeout_s: float = 120.0,
    multiple: bool | None = None,
) -> PortalScreenCastSession:
    from .linux_xwd import is_blank_png

    ensure_portal_session_env()
    existing = get_active_screencast()
    if existing is not None and existing.is_ready:
        try:
            probe = existing.capture_png()
            if not is_blank_png(probe):
                return existing
        except VDisplayError:
            pass
    stop_screencast_session()
    prepare_portal_screencast_start()
    session = PortalScreenCastSession()
    session.start(interactive=interactive, timeout_s=timeout_s, multiple=multiple)
    return session


def stop_screencast_session() -> dict[str, Any]:
    session = get_active_screencast()
    if session is None:
        return {"ok": True, "stopped": False}
    return session.stop()


def _is_retryable_screencast_error(error: str | None) -> bool:
    if not error:
        return False
    lowered = error.lower()
    return (
        "before starting" in lowered
        or "session already started" in lowered
        or "sources already selected" in lowered
        or "stale portal session" in lowered
        or "invalid session" in lowered
    )


def _pipewire_capture_timeout_s() -> float:
    raw = os.environ.get("VDISPLAY_PIPEWIRE_CAPTURE_TIMEOUT_S", "8")
    try:
        return max(2.0, min(30.0, float(raw)))
    except ValueError:
        return 8.0


def _pipewire_force_caps() -> bool:
    raw = os.environ.get("VDISPLAY_PIPEWIRE_FORCE_CAPS", "0").strip().lower()
    return raw in {"1", "true", "yes"}


def _gnome_screenshot_fallback_enabled() -> bool:
    raw = os.environ.get("VDISPLAY_SCREENCAST_GNOME_FALLBACK", "1").strip().lower()
    return raw not in {"0", "false", "no"}


def _capture_via_gnome_screenshot_region(properties: dict[str, Any]) -> bytes:
    """Fallback for GNOME Wayland when pipewiresrc cannot preroll."""
    from .linux_xwd import _capture_gnome_screenshot_png, _crop_png, is_blank_png
    from .portal import capture_portal_png

    region = _stream_properties_region(properties)
    if region is None:
        raise VDisplayError("desktop screenshot fallback requires stream region")

    errors: list[str] = []
    for label, capture_full in (
        ("portal", lambda: capture_portal_png(interactive=False, timeout_s=15.0)),
        ("gnome-screenshot", _capture_gnome_screenshot_png),
    ):
        try:
            full = capture_full()
            if is_blank_png(full):
                raise VDisplayError(f"{label} returned blank frame")
            cropped = _crop_png(
                full,
                (region["x"], region["y"], region["width"], region["height"]),
            )
            if is_blank_png(cropped):
                raise VDisplayError(f"{label} crop returned blank frame")
            return cropped
        except VDisplayError as exc:
            errors.append(f"{label}: {exc}")
    raise VDisplayError("; ".join(errors))


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


def _screencast_pipewire_fd(session: PortalScreenCastSession, *, fresh: bool = False) -> int:
    """Return a PipeWire fd for an active portal ScreenCast session."""
    if fresh or _pipewire_fresh_fd_enabled():
        return _open_screencast_pipewire_fd(session.session_path)
    fd = session.pipewire_fd
    if fd is not None and fd >= 0:
        return os.dup(fd)
    return _open_screencast_pipewire_fd(session.session_path)


def _pipewire_fresh_fd_enabled() -> bool:
    raw = os.environ.get("VDISPLAY_PIPEWIRE_FRESH_FD", "0").strip().lower()
    return raw in {"1", "true", "yes"}


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
    except ImportError:
        return _start_screencast_subprocess(
            interactive=interactive,
            timeout_s=timeout_s,
            multiple=allow_multiple,
        )

    payload = _start_screencast_impl(
        interactive=interactive,
        timeout_s=timeout_s,
        multiple=allow_multiple,
    )
    if payload.get("ok"):
        return payload
    for attempt in range(4):
        if not _is_retryable_screencast_error(payload.get("error")):
            return payload
        session_path = str(payload.get("session_path") or "")
        if session_path:
            _close_screencast_session(session_path)
            _forget_screencast_path(session_path)
        _purge_stale_screencast_sessions()
        stop_screencast_session()
        import time

        time.sleep(0.25 * (attempt + 1))
        payload = _start_screencast_impl(
            interactive=interactive,
            timeout_s=timeout_s,
            multiple=allow_multiple,
        )
        if payload.get("ok"):
            return payload
    return payload


def _portal_request_path(bus, token: str) -> str:
    unique = bus.get_unique_name()[1:].replace(".", "_")
    return f"/org/freedesktop/portal/desktop/request/{unique}/{token}"


def _stream_properties(raw: Any) -> dict[str, Any]:
    if not raw:
        return {}
    return {str(key): value for key, value in dict(raw).items()}


def _stream_serial(properties: dict[str, Any], *, node_id: int | None = None) -> str | None:
    """PipeWire target-object for pipewiresrc.

    Prefers pipewire-serial (properties) if present, then portal 'id' from props,
    falling back to the provided node_id only when props have no serial/id.
    """
    serial = properties.get("pipewire-serial")
    if serial is not None:
        return str(int(serial))
    pid = properties.get("id")
    if pid is not None and str(pid) != "":
        return str(pid)
    if node_id is not None:
        return str(int(node_id))
    return None


def _stream_target(node_id: int, properties: dict[str, Any]) -> str:
    return _stream_serial(properties, node_id=node_id) or str(node_id)


def screencast_stream_region(session: PortalScreenCastSession | None) -> dict[str, int] | None:
    """Desktop region for the first portal ScreenCast stream (position + size)."""
    if session is None:
        return None
    streams = list(getattr(session, "streams", None) or [])
    if not streams:
        return None
    return _stream_properties_region(streams[0].get("properties") or {})


def screencast_stream_region_for_monitor(
    session: PortalScreenCastSession | None,
    monitor: dict[str, Any],
) -> dict[str, int] | None:
    """Best-matching portal stream region for a monitor (position + size overlap)."""
    if session is None:
        return None
    streams = list(getattr(session, "streams", None) or [])
    if not streams:
        return None

    mx = int(monitor.get("x") or 0)
    my = int(monitor.get("y") or 0)
    mw = int(monitor.get("width") or 0)
    mh = int(monitor.get("height") or 0)
    if mw <= 0 or mh <= 0:
        return screencast_stream_region(session)

    best: dict[str, int] | None = None
    best_area = 0
    for stream in streams:
        region = _stream_properties_region(stream.get("properties") or {})
        if region is None:
            continue
        sx = region["x"]
        sy = region["y"]
        sw = region["width"]
        sh = region["height"]
        ix = max(mx, sx)
        iy = max(my, sy)
        ir = min(mx + mw, sx + sw)
        ib = min(my + mh, sy + sh)
        area = max(0, ir - ix) * max(0, ib - iy)
        if area > best_area:
            best_area = area
            best = region
    return best or screencast_stream_region(session)


def screencast_stream_region_for_index(
    session: PortalScreenCastSession | None, index: int
) -> dict[str, int] | None:
    """Region (position + size) for a specific stream index (0-based into session.streams).

    When we have already decided (via matching) that a particular stream index
    corresponds to a monitor/source, this gives the authoritative rect for the
    frame we actually captured, instead of re-running the best-overlap heuristic.
    """
    if session is None:
        return None
    streams = list(getattr(session, "streams", None) or [])
    if 0 <= index < len(streams):
        return _stream_properties_region(streams[index].get("properties") or {})
    return None


def _stream_properties_size(properties: dict[str, Any]) -> tuple[int, int] | None:
    region = _stream_properties_region(properties)
    if region is None:
        return None
    return region["width"], region["height"]


def _stream_properties_region(properties: dict[str, Any]) -> dict[str, int] | None:
    position = properties.get("position") or [0, 0]
    size = properties.get("size") or []
    if len(position) < 2 or len(size) < 2:
        return None
    width = int(size[0])
    height = int(size[1])
    if width <= 0 or height <= 0:
        return None
    return {
        "x": int(position[0]),
        "y": int(position[1]),
        "width": width,
        "height": height,
    }


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


def _portal_response_error(code: int, operation: str) -> str | None:
    if code == 0:
        return None
    if code == 1:
        return f"user cancelled {operation}"
    if code == 2:
        if operation == "screencast source selection":
            return (
                "screencast denied (Screen Recording permission missing). "
                "GNOME: Settings → Privacy → Screen Recording → enable vdisplay-agent."
            )
        if operation == "screencast session creation":
            return (
                "screencast session creation denied (portal rejected CreateSession). "
                "GNOME: Settings → Privacy → Screen Recording → enable python3 and "
                "vdisplay-agent, then retry from a local GUI terminal (not SSH)."
            )
        return f"{operation} denied"
    return f"{operation.capitalize()} failed with response={code}"


def _parse_start_streams(results: dict[str, Any]) -> tuple[list[int], list[str], list[dict[str, Any]]] | None:
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
        return None
    return node_ids, stream_targets, parsed_streams


def _open_pipewire_fd(screencast, session_path: str) -> int | None:
    try:
        import dbus

        fd = _dbus_fd(
            screencast.OpenPipeWireRemote(
                session_path,
                dbus.Dictionary({}, signature="sv"),
            )
        )
    except Exception:
        return None
    if fd < 0:
        return None
    owned_fd = os.dup(fd)
    os.close(fd)
    _ensure_fd_inheritable(owned_fd)
    return owned_fd


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
    _purge_stale_screencast_sessions()

    def next_token(label: str) -> str:
        token_counter["n"] += 1
        return f"vdisplay_sc_{label}_{token_counter['n']}"

    def fail(error: str) -> None:
        state["ok"] = False
        state["error"] = error
        loop.quit()

    def on_start(response, results) -> None:
        error = _portal_response_error(int(response), "screencast start")
        if error:
            fail(error)
            return
        parsed = _parse_start_streams(results)
        if parsed is None:
            fail("screencast Start returned no pipewire streams")
            return
        node_ids, stream_targets, parsed_streams = parsed
        owned_fd = _open_pipewire_fd(screencast, state["session_path"])
        if owned_fd is None:
            fail("OpenPipeWireRemote failed or returned no fd")
            return
        state["streams"] = parsed_streams
        state["node_ids"] = node_ids
        state["stream_targets"] = stream_targets
        state["pipewire_fd"] = owned_fd
        # Capture and persist restore_token for dialog-free restarts (portal v4+)
        token = str(results.get("restore_token") or "").strip()
        if token:
            state["restore_token"] = token
            _save_restore_token(token)
        state["ok"] = True
        loop.quit()

    def on_select(response, results) -> None:
        error = _portal_response_error(int(response), "screencast source selection")
        if error:
            fail(error)
            return
        state["stage"] = "start"
        start_token = next_token("start")
        start_path = _portal_request_path(bus, start_token)
        listen(start_path, on_start)
        try:
            screencast.Start(
                state["session_path"],
                "",
                {"handle_token": start_token},
            )
        except Exception as exc:
            msg = str(exc)
            if "session already started" in msg.lower():
                _close_screencast_session(state["session_path"])
                fail(f"screencast Start failed: stale portal session — close and retry ({exc})")
            else:
                fail(f"screencast Start failed: {exc}")

    def on_create(response, results) -> None:
        error = _portal_response_error(int(response), "screencast session creation")
        if error:
            fail(error)
            return
        session_path = str(results.get("session_handle") or "")
        if not session_path:
            fail("CreateSession returned no session_handle")
            return
        state["session_path"] = session_path
        _remember_screencast_path(session_path)
        state["stage"] = "select"
        select_token = next_token("select")
        select_path = _portal_request_path(bus, select_token)
        listen(select_path, on_select)
        try:
            select_opts: dict[str, Any] = {
                "handle_token": select_token,
                "types": dbus.UInt32(1),
                "multiple": dbus.Boolean(multiple),
                "cursor_mode": dbus.UInt32(int(os.environ.get("VDISPLAY_SCREENCAST_CURSOR", "2"))),
                "persist_mode": dbus.UInt32(2),
            }
            saved_token = _load_restore_token()
            if saved_token:
                select_opts["restore_token"] = dbus.String(saved_token)
            screencast.SelectSources(
                session_path,
                select_opts,
            )
        except Exception as exc:
            msg = str(exc)
            if "Sources already selected" in msg:
                on_select(0, {})
            elif "before starting" in msg.lower() or "invalid session" in msg.lower():
                _close_screencast_session(session_path)
                _forget_screencast_path(session_path)
                fail(f"SelectSources failed: stale portal session — close and retry ({exc})")
            else:
                fail(f"SelectSources failed: {exc}")

    ensure_portal_session_env()
    ok, hint = portal_session_env_status()
    if not ok:
        return {"ok": False, "error": hint}

    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    proxy = bus.get_object("org.freedesktop.portal.Desktop", "/org/freedesktop/portal/desktop")
    screencast = dbus.Interface(proxy, dbus_interface="org.freedesktop.portal.ScreenCast")

    pending_receivers: list[tuple[Any, str]] = []

    def listen(request_path: str, callback) -> None:
        _listen_portal_request(bus, request_path, callback, pending_receivers)

    create_token = next_token("create")
    create_path = _portal_request_path(bus, create_token)
    listen(create_path, on_create)

    import uuid

    try:
        screencast.CreateSession(
            {
                "handle_token": create_token,
                "session_handle_token": f"vdisplay_sc_{uuid.uuid4().hex[:8]}",
            }
        )
    except dbus.exceptions.DBusException as exc:
        _purge_portal_request_receivers(bus, pending_receivers)
        return {"ok": False, "error": f"CreateSession failed: {exc}"}

    GLib.timeout_add_seconds(max(1, int(timeout_s)), lambda: fail(f"screencast timed out after {timeout_s}s") or False)
    try:
        loop.run()
    finally:
        _purge_portal_request_receivers(bus, pending_receivers)

    if state.get("ok"):
        return {
            "ok": True,
            "session_path": state["session_path"],
            "streams": state.get("streams") or [],
            "node_ids": state.get("node_ids") or [],
            "stream_targets": state.get("stream_targets") or [],
            "pipewire_fd": state.get("pipewire_fd"),
            "_portal_bus": bus,
        }
    payload = {"ok": False, "error": state.get("error") or "screencast failed"}
    if state.get("session_path"):
        payload["session_path"] = state["session_path"]
    return payload


def _remove_portal_request_receiver(bus, handler, request_path: str) -> None:
    try:
        bus.remove_signal_receiver(
            handler,
            dbus_interface="org.freedesktop.portal.Request",
            signal_name="Response",
            path=str(request_path),
        )
    except Exception:
        pass


def _purge_portal_request_receivers(bus, pending: list[tuple[Any, str]]) -> None:
    for handler, request_path in list(pending):
        _remove_portal_request_receiver(bus, handler, request_path)
    pending.clear()


def _listen_portal_request(
    bus,
    request_path,
    callback,
    pending: list[tuple[Any, str]],
) -> None:
    path = str(request_path)

    def on_response(response, results) -> None:
        _remove_portal_request_receiver(bus, on_response, path)
        pending[:] = [(handler, req_path) for handler, req_path in pending if handler is not on_response]
        callback(response, results)

    bus.add_signal_receiver(
        on_response,
        dbus_interface="org.freedesktop.portal.Request",
        signal_name="Response",
        path=path,
    )
    pending.append((on_response, path))


def _close_screencast_session(session_path: str) -> None:
    path = str(session_path or "").strip()
    if not path:
        return
    import time

    for attempt in range(3):
        try:
            import dbus

            bus = dbus.SessionBus()
            session = bus.get_object("org.freedesktop.portal.Desktop", path)
            iface = dbus.Interface(session, dbus_interface="org.freedesktop.portal.Session")
            iface.Close()
            return
        except Exception:
            if attempt < 2:
                time.sleep(0.1 * (attempt + 1))


def _retryable_capture_error(err: str) -> bool:
    lowered = err.lower()
    return (
        "target not found" in lowered
        or "timed out" in lowered
        or "doesn't want to preroll" in lowered
        or "waiting for frame" in lowered
        or "failed to set pipeline" in lowered
        or "paused" in lowered
    )


def _capture_pipewire_stream(
    *,
    pipewire_fd: int,
    node_id: int,
    target_object: str | None = None,
    portal_stream_id: str | None = None,
    stream_size: tuple[int, int] | None = None,
    timeout_s: float = 30.0,
) -> bytes:
    strategies: list[tuple[str, str | None]] = []
    seen: set[str] = set()

    def _add(label: str, tobj: str | None) -> None:
        key = tobj if tobj is not None else f"path:{node_id}"
        if key in seen:
            return
        seen.add(key)
        strategies.append((label, tobj))

    _add(f"path={node_id}", None)
    if portal_stream_id and portal_stream_id != str(node_id):
        _add(f"target-object={portal_stream_id}", portal_stream_id)
    _add("default-stream", "__default__")

    width, height = stream_size if stream_size else (None, None)
    if not _pipewire_force_caps():
        width, height = None, None
    per_try = max(3.0, min(timeout_s, timeout_s / max(1, len(strategies))))
    errors: list[str] = []
    for label, tobj in strategies:
        try:
            return _capture_pipewire_stream_once(
                pipewire_fd=pipewire_fd,
                node_id=node_id,
                target_object=tobj,
                width=width,
                height=height,
                timeout_s=per_try,
            )
        except subprocess.TimeoutExpired:
            errors.append(f"{label}: timed out after {per_try:.1f}s")
        except VDisplayError as exc:
            err = str(exc)
            errors.append(f"{label}: {err[:160]}")
            if not _retryable_capture_error(err):
                raise
    raise VDisplayError(f"gstreamer pipewire capture failed: {'; '.join(errors)}")


def _capture_pipewire_stream_once(
    *,
    pipewire_fd: int,
    node_id: int,
    target_object: str | None = None,
    width: int | None = None,
    height: int | None = None,
    timeout_s: float = 30.0,
) -> bytes:
    cap_fd = os.dup(pipewire_fd)
    try:
        _ensure_fd_inheritable(cap_fd)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            out = Path(tmp.name)
        try:
            return _capture_pipewire_frame_gst_launch(
                cap_fd,
                node_id,
                target_object,
                out,
                width=width,
                height=height,
                timeout_s=timeout_s,
            )
        finally:
            out.unlink(missing_ok=True)
    finally:
        os.close(cap_fd)


def _pipewire_capture_pipeline_tail(
    *,
    width: int | None = None,
    height: int | None = None,
    sink: str = "appsink name=sink sync=false max-buffers=1 drop=true",
) -> str:
    return (
        _pipewire_video_caps(width, height)
        + " ! queue max-size-buffers=1 max-size-time=0 max-size-bytes=0 leaky=downstream"
        + " ! videoconvert ! pngenc ! "
        + sink
    )


def _capture_pipewire_frame_gi_threaded(
    cap_fd: int,
    node_id: int,
    target_object: str | None,
    out: Path,
    *,
    width: int | None = None,
    height: int | None = None,
    timeout_s: float,
) -> bool:
    result = {"ok": False}
    done = threading.Event()

    def _worker() -> None:
        try:
            result["ok"] = _capture_pipewire_frame_gi(
                cap_fd,
                node_id,
                target_object,
                out,
                width=width,
                height=height,
                timeout_s=timeout_s,
            )
        finally:
            done.set()

    threading.Thread(target=_worker, daemon=True, name="vdisplay-pw-gi-capture").start()
    if not done.wait(timeout=timeout_s + 2.0):
        return False
    return bool(result["ok"])


def _pipewire_video_caps(width: int | None, height: int | None) -> str:
    if width and height and width > 0 and height > 0:
        return f" ! video/x-raw,width={int(width)},height={int(height)}"
    return ""


def _pipewiresrc_target_props(
    *,
    cap_fd: int,
    node_id: int,
    target_object: str | None,
) -> str:
    props = f"fd={cap_fd} always-copy=true do-timestamp=true keepalive-time=100"
    if target_object == "__default__":
        return props
    if target_object:
        return props + f" target-object={target_object}"
    return props + f" path={node_id}"


def _capture_pipewire_frame_gi(
    cap_fd: int,
    node_id: int,
    target_object: str | None,
    out: Path,
    *,
    width: int | None = None,
    height: int | None = None,
    timeout_s: float,
) -> bool:
    """Capture one frame in-process (avoids subprocess pass_fds issues in keeper)."""
    try:
        _ensure_portal_deps()
        import gi

        gi.require_version("Gst", "1.0")
        from gi.repository import Gst
    except ImportError:
        return False

    Gst.init(None)
    props = _pipewiresrc_target_props(
        cap_fd=cap_fd,
        node_id=node_id,
        target_object=target_object,
    )
    try:
        pipe = Gst.parse_launch(
            "pipewiresrc "
            + props
            + _pipewire_capture_pipeline_tail(width=width, height=height)
        )
        sink = pipe.get_by_name("sink")
        pipe.set_state(Gst.State.PLAYING)
        sample = sink.emit("try-pull-sample", int(timeout_s * 1_000_000_000))
        pipe.set_state(Gst.State.NULL)
    except Exception:
        return False
    if sample is None:
        return False
    buf = sample.get_buffer()
    ok, info = buf.map(Gst.MapFlags.READ)
    if not ok:
        return False
    try:
        data = bytes(info.data)
    finally:
        buf.unmap(info)
    if len(data) < 64:
        return False
    out.write_bytes(data)
    return True


_CAPTURE_FRAME_SCRIPT = r'''
import sys

fd = int(sys.argv[1])
node_id = int(sys.argv[2])
target = sys.argv[3]
out_path = sys.argv[4]
timeout_s = float(sys.argv[5])
width = int(sys.argv[6] or 0)
height = int(sys.argv[7] or 0)

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst

Gst.init(None)
props = f"fd={fd} always-copy=1 num-buffers=1 do-timestamp=true keepalive-time=100"
if target == "__default__":
    pass
elif target:
    props += f" target-object={target}"
else:
    props += f" path={node_id}"
caps = f" ! video/x-raw,width={width},height={height}" if width > 0 and height > 0 else ""
pipe = Gst.parse_launch(
    "pipewiresrc " + props + caps
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
    width: int | None = None,
    height: int | None = None,
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
                    str(width or 0),
                    str(height or 0),
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
    if completed.stderr or completed.stdout:
        hint = (completed.stderr or completed.stdout).strip().splitlines()[-1][:200]
        if hint:
            import sys

            print(f"vdisplay: pipewire gi capture failed: {hint}", file=sys.stderr)
    return False


def _capture_pipewire_frame_gst_launch(
    cap_fd: int,
    node_id: int,
    target_object: str | None,
    out: Path,
    *,
    width: int | None = None,
    height: int | None = None,
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
        "always-copy=true",
        "do-timestamp=true",
        "keepalive-time=100",
    ]
    if target_object == "__default__":
        pass
    elif target_object:
        src_args.append(f"target-object={target_object}")
    else:
        src_args.append(f"path={node_id}")
    pipeline = [*src_args]
    if width and height and width > 0 and height > 0:
        pipeline.extend(["!", f"video/x-raw,width={int(width)},height={int(height)}"])
    pipeline.extend(
        [
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
        ]
    )
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="pass_fds overriding close_fds", category=RuntimeWarning)
        try:
            completed = subprocess.run(
                [
                    gst,
                    "-e",
                    *pipeline,
                ],
                capture_output=True,
                timeout=timeout_s,
                check=False,
                close_fds=False,
                pass_fds=tuple(sorted({0, 1, 2, cap_fd})),
            )
        except subprocess.TimeoutExpired as exc:
            raise VDisplayError(
                f"gstreamer pipewire capture timed out after {timeout_s:.1f}s"
            ) from exc
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
    env.update(ensure_portal_session_env())
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
    result.pop("_portal_bus", None)
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
