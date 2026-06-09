"""Host and session capture for the broker."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from vdisplay.capture.host import capture_all_monitors, capture_host_to_file
from vdisplay.exceptions import VDisplayError

from ..session_store import SessionStore


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
    bulk = capture_all_monitors(
        display=body.get("display"),
        out_dir=out_dir,
        target=body.get("target"),
        prefer_mirror=bool(body.get("prefer_mirror")),
        screencast_session=store.screencast,
    )
    return {"ok": True, "out_dir": out_dir, **bulk}


def _capture_host(store: SessionStore, body: dict[str, Any]) -> dict[str, Any]:
    output = body.get("output") or body.get("path")
    if not output:
        raise VDisplayError("capture requires session_id, all_monitors, or output path")
    try:
        meta = capture_host_to_file(
            output,
            monitor=int(body.get("monitor") or 1),
            display=body.get("display"),
            source=body.get("source"),
            target=body.get("target"),
            prefer_mirror=bool(body.get("prefer_mirror")),
            screencast_session=store.screencast,
        )
    except VDisplayError:
        if store.screencast is not None and not store.screencast.is_ready:
            store.screencast = None
        raise
    png = Path(meta["path"]).read_bytes()
    meta["ok"] = True
    meta["png_base64"] = base64.b64encode(png).decode("ascii")
    return meta
