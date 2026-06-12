"""Host and session capture for the broker."""

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any

from vdisplay.capture.host import capture_all_monitors, capture_host_to_file
from vdisplay.exceptions import VDisplayError

from ..session_store import SessionStore
from . import sessions as session_svc
from .screencast_recovery import is_recoverable_screencast_error, try_recover_screencast


def capture_frame(store: SessionStore, body: dict[str, Any]) -> dict[str, Any]:
    session_id = body.get("session_id")
    if session_id:
        return _capture_session(store, str(session_id), body)
    if body.get("all_monitors"):
        return _capture_all_monitors(store, body)
    return _capture_host(store, body)


def _capture_session(store: SessionStore, session_id: str, body: dict[str, Any]) -> dict[str, Any]:
    record = store.get(session_id)
    png = record.handle.screenshot_bytes()
    result: dict[str, Any] = {
        "ok": True,
        "session_id": session_id,
        "mode": record.kind,
        "png_base64": base64.b64encode(png).decode("ascii"),
        "bytes": len(png),
    }
    output = body.get("output") or body.get("path")
    if output:
        out = Path(output).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(png)
        result["path"] = str(out.resolve())
    return result


def _capture_all_monitors(store: SessionStore, body: dict[str, Any]) -> dict[str, Any]:
    out_dir = body.get("out_dir") or str(Path("/tmp/vdisplay-agent-captures"))
    bridge_captures = store.browser_bridge.copy_all_fresh(out_dir, display=body.get("display"))
    if bridge_captures:
        return {
            "ok": True,
            "out_dir": out_dir,
            "count": len(bridge_captures),
            "captures": bridge_captures,
            "method": "browser-bridge",
            "keeper_mode": "browser_bridge",
        }
    bulk = capture_all_monitors(
        display=body.get("display"),
        out_dir=out_dir,
        target=body.get("target"),
        prefer_mirror=bool(body.get("prefer_mirror")),
        screencast_session=store.screencast,
    )
    return {"ok": True, "out_dir": out_dir, **bulk}


def _region_from_body(body: dict[str, Any]) -> tuple[int, int, int, int] | None:
    raw = body.get("region")
    if raw is None:
        return None
    if isinstance(raw, dict):
        values = (raw.get("x"), raw.get("y"), raw.get("width"), raw.get("height"))
    elif isinstance(raw, (list, tuple)) and len(raw) == 4:
        values = tuple(raw)
    else:
        return None
    if None in values:
        return None
    x, y, width, height = (int(values[0]), int(values[1]), int(values[2]), int(values[3]))
    if width <= 0 or height <= 0:
        return None
    return x, y, width, height


def _capture_host(store: SessionStore, body: dict[str, Any]) -> dict[str, Any]:
    output = body.get("output") or body.get("path")
    if not output:
        raise VDisplayError("capture requires session_id, all_monitors, or output path")
    region = _region_from_body(body)
    bridge_meta = store.browser_bridge.copy_fresh(
        output,
        source=body.get("source"),
        display=body.get("display"),
        region=region,
    )
    if bridge_meta is not None:
        png = Path(bridge_meta["path"]).read_bytes()
        bridge_meta["ok"] = True
        bridge_meta["png_base64"] = base64.b64encode(png).decode("ascii")
        if store.screencast is not None:
            session_svc.clear_screencast_capture_failure(store)
        return bridge_meta
    if store.screencast is not None or not _electron_share_enabled():
        _raise_if_wayland_screencast_keeper_missing(store)
    try:
        meta = capture_host_to_file(
            output,
            monitor=int(body.get("monitor") or 1),
            display=body.get("display"),
            source=body.get("source"),
            target=body.get("target"),
            prefer_mirror=bool(body.get("prefer_mirror")),
            screencast_session=store.screencast,
            region=region,
        )
    except IndexError as exc:
        if store.screencast is not None:
            session_svc.mark_screencast_capture_failed(store, exc)
            raise VDisplayError(
                "screencast stream mapping failed inside vdisplay-agent "
                f"({exc}). Restart ScreenCast with `vdisplay agent screencast start --force`, "
                "choose All Screens/the target monitor, then run "
                "`vdisplay agent screencast probe --via-agent --source <monitor>`."
            ) from exc
        raise
    except VDisplayError as exc:
        if store.screencast is not None and not store.screencast.is_ready:
            store.screencast = None
            session_svc.clear_screencast_capture_failure(store)
        if is_recoverable_screencast_error(exc) and not body.get("_screencast_recovered"):
            if try_recover_screencast(store, interactive_preferred=False):
                return _capture_host(store, {**body, "_screencast_recovered": True})
            from .screencast_recovery import screencast_recovery_cooldown_remaining

            cooldown = screencast_recovery_cooldown_remaining()
            hint = (
                "screencast auto-start failed — run once: vdisplay agent screencast start "
                "(after agent restart if you see DBus LimitsExceeded / max_match_rules)"
            )
            if cooldown > 0:
                hint += f" (next auto-retry in {int(cooldown)}s)"
            if store.screencast is not None:
                session_svc.mark_screencast_capture_failed(store, exc)
            raise VDisplayError(f"{exc} — {hint}") from exc
        # Non-recoverable case or recovery not taken: re-raise the original error.
        # This prevents falling through to code that assumes 'meta' (or 'png')
        # was assigned in the try block.
        if store.screencast is not None:
            session_svc.mark_screencast_capture_failed(store, exc)
        raise
    # On success path only: capture_host_to_file wrote the PNG and returned meta
    # (including "path"). We attach the wire fields here.
    png = Path(meta["path"]).read_bytes()
    meta["ok"] = True
    meta["png_base64"] = base64.b64encode(png).decode("ascii")
    if store.screencast is not None:
        session_svc.clear_screencast_capture_failure(store)
    return meta


def _electron_share_enabled() -> bool:
    try:
        from vdisplay.capture.electron_share import electron_share_enabled

        return electron_share_enabled()
    except Exception:
        return False


def _raise_if_wayland_screencast_keeper_missing(store: SessionStore) -> None:
    session = store.screencast
    if session is None or not getattr(session, "is_ready", False):
        return
    if os.environ.get("VDISPLAY_ALLOW_DIRECT_SCREENCAST_CAPTURE", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }:
        return
    try:
        from types import MethodType

        if not isinstance(getattr(session, "capture_png", None), MethodType):
            return
    except Exception:
        pass
    try:
        from vdisplay.capture.linux_xwd import _is_wayland_session
    except Exception:
        return
    if not _is_wayland_session():
        return
    try:
        from vdisplay.capture.screencast_keeper import (
            keeper_capture_ready,
            read_keeper_state,
            session_uses_keeper,
        )

        if session_uses_keeper(session) and keeper_capture_ready(
            read_keeper_state(),
            socket_path=str(getattr(session, "keeper_socket_path", "") or "") or None,
            timeout_s=0.2,
        ):
            return
    except Exception:
        pass
    raise VDisplayError(
        "screencast portal session is active, but frame keeper is not running. "
        "Run `vdisplay agent screencast start --force` from a local GNOME terminal, "
        "choose All Screens/the IDE monitor, then verify with "
        "`vdisplay agent screencast probe --via-agent --source <monitor>`."
    )
