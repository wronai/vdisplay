"""Unified desktop ↔ capture-local coordinate mapping (multi-monitor, rotation, ScreenCast)."""

from __future__ import annotations

from typing import Any

from .coordinate_rotation import (
    aspect_mismatch as _aspect_mismatch,
    local_to_region_coords as _local_to_region_coords,
    region_rel_to_local as _region_rel_to_local,
)
from .screencast_stream_meta import enrich_screencast_stream_meta, stream_bounds_from_meta


def global_pointer_coords(
    local_x: int,
    local_y: int,
    capture_meta: dict[str, Any] | None,
    *,
    display: str | None = None,
) -> tuple[int, int, dict[str, Any]]:
    """Translate OCR/template pixel coords into desktop space for ydotool."""
    meta = enrich_screencast_stream_meta(dict(capture_meta or {}))
    png_w = int(meta.get("width") or 0)
    png_h = int(meta.get("height") or 0)
    region = meta.get("region") or {}

    if region:
        return _global_from_region(
            local_x,
            local_y,
            meta=meta,
            region=region,
            png_w=png_w,
            png_h=png_h,
            display=display,
        )

    source = str(meta.get("source") or meta.get("monitor_name") or "")
    if source:
        monitor = _monitor_by_name(display, source)
        if monitor is not None:
            return _global_from_monitor(local_x, local_y, monitor=monitor, png_w=png_w, png_h=png_h)

    return local_x, local_y, {"mapping": "local"}


def _get_stream_region(meta: dict[str, Any]) -> dict[str, Any]:
    """Return the stream/region bounds if this capture uses a screencast stream or full frame."""
    region = stream_bounds_from_meta(meta) or {}
    if not region or not (meta.get("screencast_stream") or meta.get("screencast_full_frame")):
        return {}
    return region


def global_point_to_capture_local(
    global_x: int,
    global_y: int,
    capture_meta: dict[str, Any],
    *,
    display: str | None = None,
) -> tuple[int, int]:
    """Translate desktop coordinates into PNG pixel space for screencast crops."""
    meta = enrich_screencast_stream_meta(dict(capture_meta))
    png_w = int(meta.get("width") or 0)
    png_h = int(meta.get("height") or 0)
    region = _get_stream_region(meta)
    if not region:
        return global_x, global_y

    origin_x = int(region.get("x") or 0)
    origin_y = int(region.get("y") or 0)
    region_w = int(region.get("width") or png_w or 1)
    region_h = int(region.get("height") or png_h or 1)
    rotation = meta.get("rotation") or _rotation_for_monitor(
        display or meta.get("display"),
        meta.get("monitor_name") or meta.get("source"),
    )
    rel_x = global_x - origin_x
    rel_y = global_y - origin_y
    return _region_rel_to_local(
        rel_x,
        rel_y,
        png_w=png_w,
        png_h=png_h,
        region_w=region_w,
        region_h=region_h,
        rotation=rotation,
    )


def _clip_global_to_stream(
    gx: int, gy: int, gw: int, gh: int,
    origin_x: int, origin_y: int, stream_w: int, stream_h: int,
) -> tuple[int, int, int, int] | None:
    """Clip global rect to the stream region; return None if empty after clip."""
    clip_left = max(gx, origin_x)
    clip_top = max(gy, origin_y)
    clip_right = min(gx + gw, origin_x + stream_w)
    clip_bottom = min(gy + gh, origin_y + stream_h)
    if clip_right <= clip_left or clip_bottom <= clip_top:
        return None
    return clip_left, clip_top, clip_right, clip_bottom


def _bounds_from_corners(
    corners: tuple[tuple[int, int], ...],
    *,
    png_w: int,
    png_h: int,
) -> tuple[int, int, int, int] | None:
    xs = [point[0] for point in corners]
    ys = [point[1] for point in corners]
    left = max(0, min(xs))
    top = max(0, min(ys))
    right = min(png_w, max(xs))
    bottom = min(png_h, max(ys))
    width = right - left
    height = bottom - top
    if width <= 0 or height <= 0:
        return None
    return left, top, width, height


def _map_corners_to_local(
    corners: tuple[tuple[int, int], ...],
    meta: dict[str, Any],
    display: str | None,
) -> list[tuple[int, int]]:
    return [
        global_point_to_capture_local(x, y, meta, display=display or meta.get("display"))
        for x, y in corners
    ]


def global_region_to_capture_local(
    region: tuple[int, int, int, int],
    capture_meta: dict[str, Any],
    *,
    display: str | None = None,
) -> tuple[int, int, int, int] | None:
    """Map a global desktop crop rect into PNG-local coordinates."""
    meta = enrich_screencast_stream_meta(dict(capture_meta))
    if not meta.get("screencast_full_frame"):
        return region

    png_w = int(meta.get("width") or 0)
    png_h = int(meta.get("height") or 0)
    if png_w <= 0 or png_h <= 0:
        return None

    stream = stream_bounds_from_meta(meta) or {}
    origin_x = int(stream.get("x") or 0)
    origin_y = int(stream.get("y") or 0)
    stream_w = int(stream.get("width") or png_w or 1)
    stream_h = int(stream.get("height") or png_h or 1)

    gx, gy, gw, gh = region
    clipped = _clip_global_to_stream(gx, gy, gw, gh, origin_x, origin_y, stream_w, stream_h)
    if clipped is None:
        return None
    clip_left, clip_top, clip_right, clip_bottom = clipped

    corners = _map_corners_to_local(
        (
            (clip_left, clip_top),
            (clip_right, clip_top),
            (clip_left, clip_bottom),
            (clip_right, clip_bottom),
        ),
        meta,
        display,
    )
    return _bounds_from_corners(tuple(corners), png_w=png_w, png_h=png_h)


def _global_from_region(
    local_x: int,
    local_y: int,
    *,
    meta: dict[str, Any],
    region: dict[str, Any],
    png_w: int,
    png_h: int,
    display: str | None,
) -> tuple[int, int, dict[str, Any]]:
    origin_x = int(region.get("x") or 0)
    origin_y = int(region.get("y") or 0)
    region_w = int(region.get("width") or png_w or 1)
    region_h = int(region.get("height") or png_h or 1)
    rotation = meta.get("rotation") or _rotation_for_monitor(display, meta.get("monitor") or meta.get("source"))
    rel_x, rel_y, scale_x, scale_y = _local_to_region_coords(
        local_x,
        local_y,
        png_w=png_w,
        png_h=png_h,
        region_w=region_w,
        region_h=region_h,
        rotation=rotation,
        allow_1to1_fallback=False,
    )
    mapping = "screencast-stream" if meta.get("screencast_stream") else "region"
    if rotation and rotation != "normal":
        mapping = f"{mapping}+rotation-{rotation}"
    return (
        origin_x + rel_x,
        origin_y + rel_y,
        {
            "mapping": mapping,
            "origin_x": origin_x,
            "origin_y": origin_y,
            "scale_x": scale_x,
            "scale_y": scale_y,
            "rotation": rotation,
            "local_x": local_x,
            "local_y": local_y,
            "region_rel_x": rel_x,
            "region_rel_y": rel_y,
        },
    )


def _global_from_monitor(
    local_x: int,
    local_y: int,
    *,
    monitor: dict[str, Any],
    png_w: int,
    png_h: int,
) -> tuple[int, int, dict[str, Any]]:
    origin_x = int(monitor.get("x") or 0)
    origin_y = int(monitor.get("y") or 0)
    monitor_w = int(monitor.get("width") or png_w or 1)
    monitor_h = int(monitor.get("height") or png_h or 1)
    rotation = str(monitor.get("rotation") or "normal")
    rel_x, rel_y, scale_x, scale_y = _local_to_region_coords(
        local_x,
        local_y,
        png_w=png_w,
        png_h=png_h,
        region_w=monitor_w,
        region_h=monitor_h,
        rotation=rotation,
        allow_1to1_fallback=True,
    )
    mapping = "monitor"
    if rotation != "normal":
        mapping = f"monitor+rotation-{rotation}"
    elif _aspect_mismatch(monitor_w, monitor_h, png_w, png_h):
        mapping = "monitor-1:1"
    source = str(monitor.get("name") or "")
    return (
        origin_x + rel_x,
        origin_y + rel_y,
        {
            "mapping": mapping,
            "monitor": source,
            "origin_x": origin_x,
            "origin_y": origin_y,
            "scale_x": scale_x,
            "scale_y": scale_y,
            "rotation": rotation,
            "local_x": local_x,
            "local_y": local_y,
            "region_rel_x": rel_x,
            "region_rel_y": rel_y,
        },
    )


def _rotation_for_monitor(display: str | None, name: str | None) -> str | None:
    if not name:
        return None
    monitor = _monitor_by_name(display, name)
    if monitor is None:
        return None
    return str(monitor.get("rotation") or "normal")


def _monitor_by_name(display: str | None, name: str) -> dict[str, Any] | None:
    from ..input.coords import _monitor_by_name as lookup

    return lookup(display, name)
