"""Portal ScreenCast stream bounds attached to capture metadata."""

from __future__ import annotations

from typing import Any

from ..exceptions import VDisplayError


def stream_bounds_from_meta(meta: dict[str, Any]) -> dict[str, int] | None:
    """Return portal ScreenCast desktop bounds without confusing crop/request regions."""
    raw = meta.get("screencast_stream_region")
    if isinstance(raw, dict):
        return _normalize_region(raw)

    if meta.get("screencast_stream") or meta.get("screencast_full_frame"):
        region = meta.get("region")
        requested = meta.get("requested_region")
        if isinstance(region, dict) and region != requested:
            normalized = _normalize_region(region)
            if normalized is not None:
                return normalized
        return resolve_screencast_stream_region()
    return None


def global_point_in_stream_bounds(
    global_x: int,
    global_y: int,
    capture_meta: dict[str, Any],
) -> bool:
    stream = stream_bounds_from_meta(capture_meta)
    if stream is None:
        return True
    left = int(stream["x"])
    top = int(stream["y"])
    right = left + int(stream["width"])
    bottom = top + int(stream["height"])
    return left <= global_x < right and top <= global_y < bottom


def enrich_screencast_stream_meta(meta: dict[str, Any]) -> dict[str, Any]:
    """Attach portal stream position/size when capture used a full ScreenCast frame."""
    meta = dict(meta)
    if meta.get("screencast_stream") and isinstance(meta.get("region"), dict):
        meta.setdefault("screencast_stream_region", dict(meta["region"]))
    if meta.get("screencast_stream_region") or not meta.get("screencast_full_frame"):
        return meta
    stream_region = resolve_screencast_stream_region()
    if stream_region is not None:
        meta["screencast_stream_region"] = stream_region
        meta.setdefault("region", stream_region)
        meta["screencast_stream"] = True
    return meta


def resolve_screencast_stream_region() -> dict[str, int] | None:
    from .portal_screencast import get_active_screencast, screencast_stream_region

    region = screencast_stream_region(get_active_screencast())
    if region is not None:
        return region
    return region_from_agent_screencast_status()


def region_from_agent_screencast_status() -> dict[str, int] | None:
    from ..agent_config import resolve_agent_url
    from ..client import AgentClient

    agent_url = resolve_agent_url(allow_auto=True)
    if not agent_url:
        return None
    try:
        status = AgentClient(agent_url).screencast_status()
    except VDisplayError:
        return None
    payload = status.get("data") if isinstance(status.get("data"), dict) else status
    streams = list((payload or {}).get("streams") or [])
    if not streams:
        return None
    properties = streams[0].get("properties") or {}
    position = properties.get("position") or [0, 0]
    size = properties.get("size") or []
    if len(position) < 2 or len(size) < 2:
        return None
    return _normalize_region({"x": position[0], "y": position[1], "width": size[0], "height": size[1]})


def _normalize_region(raw: dict[str, Any]) -> dict[str, int] | None:
    width = int(raw.get("width") or 0)
    height = int(raw.get("height") or 0)
    if width <= 0 or height <= 0:
        return None
    return {
        "x": int(raw.get("x") or 0),
        "y": int(raw.get("y") or 0),
        "width": width,
        "height": height,
    }
