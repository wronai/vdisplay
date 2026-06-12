"""Start portal ScreenCast through keeper + vdisplay-agent broker."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from ...capture.portal_screencast import portal_session_env_status
from ...capture.screencast_keeper import (
    keeper_capture_ready,
    read_keeper_state,
    request_keeper_capture,
    spawn_keeper,
    stop_keeper,
)
from ...exceptions import VDisplayError
from ..env_defaults import env_float_value

_COOLDOWN_FILE = Path(os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}") / "vdisplay-screencast-last-start"
_LOCAL_START_COOLDOWN_S = max(30.0, env_float_value("VDISPLAY_SCREENCAST_LOCAL_START_COOLDOWN_S", default=60.0))
_KEEPER_START_FRAME_TIMEOUT_S = max(
    15.0,
    env_float_value("VDISPLAY_KEEPER_START_FRAME_TIMEOUT_S", default=45.0),
)


def _local_start_cooldown_remaining() -> float:
    try:
        last = float(_COOLDOWN_FILE.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return 0.0
    elapsed = time.time() - last
    return max(0.0, _LOCAL_START_COOLDOWN_S - elapsed)


def _mark_local_start_failure() -> None:
    try:
        _COOLDOWN_FILE.parent.mkdir(parents=True, exist_ok=True)
        _COOLDOWN_FILE.write_text(str(time.time()), encoding="utf-8")
    except OSError:
        pass


def clear_local_start_cooldown() -> None:
    try:
        _COOLDOWN_FILE.unlink(missing_ok=True)
    except OSError:
        pass


def _try_reuse_existing_screencast(status: dict[str, Any], *, force: bool) -> dict[str, Any] | None:
    if force:
        return None
    if not (status.get("active") and status.get("ready")):
        return None
    if not keeper_capture_ready():
        return None
    state = read_keeper_state() or {}
    clear_local_start_cooldown()
    return {
        **status,
        "ok": True,
        "reused": True,
        "keeper_pid": state.get("pid"),
        "keeper_socket_path": state.get("socket_path"),
    }


def _check_start_eligibility(*, interactive: bool, force: bool) -> None:
    remaining = _local_start_cooldown_remaining()
    if remaining > 0 and interactive and not force:
        raise VDisplayError(
            "screencast not ready — retry with: vdisplay agent screencast start --force "
            f"(or wait {int(remaining)}s). "
            "If the GNOME dialog never appeared, run: vdisplay agent screencast clear-cooldown"
        )
    ok, hint = portal_session_env_status()
    if not ok:
        raise VDisplayError(
            f"{hint} Run from a local GNOME terminal with DBUS_SESSION_BUS_ADDRESS set."
        )


def _stop_existing_screencast(client, status: dict[str, Any], *, force: bool) -> None:
    if force or (status.get("active") and status.get("ready")):
        stop_keeper()
        try:
            client.stop_screencast()
        except VDisplayError:
            pass


def _verify_keeper_running(*, context: str) -> dict[str, Any]:
    state = read_keeper_state()
    if state is None:
        raise VDisplayError(
            f"screencast keeper not running after {context} — "
            "run: vdisplay agent screencast start --force"
        )
    if not keeper_capture_ready(state, timeout_s=5.0):
        stop_keeper()
        raise VDisplayError(
            f"screencast keeper capture socket not ready after {context} — "
            "run: vdisplay agent screencast start --force"
        )
    _verify_keeper_frame_capture(state, context=context)
    return state


def _keeper_stream_indices(state: dict[str, Any]) -> list[int]:
    streams = state.get("streams")
    node_ids = state.get("node_ids")
    stream_count = len(streams) if isinstance(streams, list) else 0
    node_count = len(node_ids) if isinstance(node_ids, list) else 0
    return list(range(max(stream_count, node_count, 1)))


def _verify_keeper_frame_capture(state: dict[str, Any], *, context: str) -> None:
    session_path = str(state.get("session_path") or "")
    socket_path = str(state.get("socket_path") or "")
    errors: list[str] = []
    for node_index in _keeper_stream_indices(state):
        try:
            png = request_keeper_capture(
                node_index=node_index,
                session_path=session_path,
                socket_path=socket_path,
                timeout_s=_KEEPER_START_FRAME_TIMEOUT_S,
            )
        except Exception as exc:
            errors.append(f"node_index={node_index}: {exc}")
            continue
        if not png.startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append(f"node_index={node_index}: capture returned non-PNG frame")
    if not errors:
        return
    stop_keeper()
    raise VDisplayError(
        f"screencast keeper socket is ready but frame capture failed after {context}: "
        f"{'; '.join(errors)}. This is not a usable ScreenCast session; "
        "re-run `vdisplay agent screencast start --force`, choose All Screens, "
        "and inspect /tmp/vdisplay-keeper-capture.log if it repeats."
    )


def _start_via_keeper(client, *, timeout_s: float, multiple: bool | None) -> dict[str, Any]:
    payload = spawn_keeper(interactive=True, timeout_s=timeout_s, multiple=multiple)
    try:
        adopted = client.adopt_screencast(
            session_path=str(payload["session_path"]),
            streams=list(payload.get("streams") or []),
            node_ids=list(payload.get("node_ids") or []),
            stream_targets=list(payload.get("stream_targets") or []),
            multiple=multiple,
            keeper_managed=True,
            socket_path=str(payload.get("socket_path") or ""),
            runtime_dir=str(payload.get("runtime_dir") or ""),
            keeper_pid=int(payload.get("pid") or 0),
        )
    except VDisplayError:
        stop_keeper()
        _mark_local_start_failure()
        raise
    if adopted.get("active") and adopted.get("ready"):
        try:
            state = _verify_keeper_running(context="start")
        except VDisplayError:
            try:
                client.stop_screencast()
            except VDisplayError:
                pass
            _mark_local_start_failure()
            raise
        clear_local_start_cooldown()
        adopted["keeper_pid"] = state.get("pid")
        adopted["keeper_socket_path"] = state.get("socket_path")
        return adopted
    stop_keeper()
    _mark_local_start_failure()
    return adopted


def _start_via_client(client, *, timeout_s: float, multiple: bool | None) -> dict[str, Any]:
    try:
        started = client.start_screencast(
            interactive=False,
            timeout_s=timeout_s,
            multiple=multiple,
        )
    except VDisplayError:
        _mark_local_start_failure()
        raise
    if started.get("active") and started.get("ready"):
        clear_local_start_cooldown()
        return started
    _mark_local_start_failure()
    return started


def _resolve_probe_monitor(
    source: str | None,
    monitors: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, str]:
    monitor: dict[str, Any] | None = None
    if source:
        monitor = next((m for m in monitors if str(m.get("name") or "") == source), None)
        if monitor is None:
            raise VDisplayError(f"monitor not found: {source} (available: {[m.get('name') for m in monitors]})")
    elif monitors:
        monitor = monitors[0]
    source_name = str(monitor.get("name") if monitor else source or "")
    return monitor, source_name


def _probe_via_agent(
    client,
    monitor: dict[str, Any] | None,
    monitors: list[dict[str, Any]],
    source_name: str,
    output: str | None,
) -> dict[str, Any]:
    if client is None:
        raise VDisplayError("agent client required for --via-agent probe")
    out = output or "/tmp/vdisplay-probe.png"
    monitor_num = monitors.index(monitor) + 1 if monitor in monitors else 1
    payload = client.capture_frame(
        output=out,
        source=source_name or None,
        monitor=monitor_num,
    )
    payload.pop("png_base64", None)
    return {"ok": True, "via": "agent", **payload}


def _probe_via_keeper(
    session: Any,
    state: dict[str, Any],
    stream_idx: int,
    source_name: str,
) -> tuple[bytes, int, list[int], list[str]]:
    from ...capture.screencast_keeper import request_keeper_capture

    errors: list[str] = []
    tried: list[int] = []
    png: bytes | None = None
    for candidate_idx in (stream_idx, 0):
        if candidate_idx in tried:
            continue
        tried.append(candidate_idx)
        try:
            png = request_keeper_capture(
                node_index=candidate_idx,
                session_path=str(state.get("session_path") or ""),
                socket_path=str(state.get("socket_path") or ""),
            )
            stream_idx = candidate_idx
            break
        except Exception as exc:
            errors.append(f"node_index={candidate_idx}: {exc}")
            continue
    if png is None:
        raise VDisplayError(
            "keeper capture failed for source "
            f"{source_name!r} (tried indices {tried}): {'; '.join(errors)}. "
            "The chosen stream may not be producing frames; "
            "inspect /tmp/vdisplay-keeper-capture.log inside the keeper and "
            "re-run with `vdisplay agent screencast start --force`."
        )
    return png, stream_idx, tried, errors


def _build_probe_result(
    png: bytes,
    stream_idx: int,
    monitor: dict[str, Any] | None,
    props: dict[str, Any],
    state: dict[str, Any],
    source_name: str,
    tried: list[int],
) -> dict[str, Any]:
    from ...capture.portal_screencast import _stream_serial
    from ...capture.screencast_crop import png_dimensions

    width, height = png_dimensions(png)
    portal_id = props.get("id")
    node_id = state.get("node_ids", [])
    node_id = node_id[stream_idx] if stream_idx < len(node_id) else None
    return {
        "ok": True,
        "via": "keeper",
        "bytes": len(png),
        "width": width,
        "height": height,
        "source": source_name,
        "stream_index": stream_idx,
        "node_id": node_id,
        "portal_stream_id": str(portal_id) if portal_id is not None else None,
        "target_object": _stream_serial(props, node_id=node_id) if node_id is not None else _stream_serial(props),
        "keeper_pid": state.get("pid"),
        "tried_indices": tried,
    }


def probe_screencast_capture(
    *,
    source: str | None = None,
    via_agent: bool = False,
    client=None,
    output: str | None = None,
) -> dict[str, Any]:
    """Verify keeper (and optionally agent) can grab one ScreenCast frame."""
    from ...capture.host import list_monitors, resolve_host_display
    from ...capture.portal_screencast import PortalScreenCastSession
    from ...capture.screencast_stream_matching import screencast_stream_index_for_monitor

    state = read_keeper_state()
    if state is None:
        raise VDisplayError("screencast keeper not running — run: vdisplay agent screencast start --force")
    if not keeper_capture_ready(state):
        raise VDisplayError(
            "keeper capture socket not ready — run: vdisplay agent screencast start --force"
        )

    session = PortalScreenCastSession.from_portal_payload(
        {
            **state,
            "keeper_managed": True,
            "socket_path": state.get("socket_path"),
        },
        verify_remote=False,
    )
    display = resolve_host_display(os.environ.get("DISPLAY"))
    monitors = list_monitors(display)
    monitor, source_name = _resolve_probe_monitor(source, monitors)

    stream_idx = (
        screencast_stream_index_for_monitor(session, monitor, all_monitors=monitors)
        if monitor is not None
        else 0
    )
    streams = list(session.streams or [])
    stream = streams[stream_idx] if 0 <= stream_idx < len(streams) else {}
    props = stream.get("properties") or {}

    if via_agent:
        return _probe_via_agent(client, monitor, monitors, source_name, output)

    png, stream_idx, tried, _errors = _probe_via_keeper(session, state, stream_idx, source_name)
    return _build_probe_result(png, stream_idx, monitor, props, state, source_name, tried)


def start_screencast_via_agent(
    client,
    *,
    interactive: bool = True,
    timeout_s: float = 120.0,
    multiple: bool | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Run ScreenCast in a GUI-session keeper, then register it with the agent."""
    status = client.screencast_status()
    reused = _try_reuse_existing_screencast(status, force=force)
    if reused is not None:
        return reused

    _check_start_eligibility(interactive=interactive, force=force)
    _stop_existing_screencast(client, status, force=force)

    if interactive:
        return _start_via_keeper(client, timeout_s=timeout_s, multiple=multiple)
    return _start_via_client(client, timeout_s=timeout_s, multiple=multiple)
