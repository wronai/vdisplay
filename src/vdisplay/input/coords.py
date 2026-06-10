"""Map screenshot-local vision bounds to global desktop coordinates."""

from __future__ import annotations

from typing import Any


def global_pointer_coords(
    local_x: int,
    local_y: int,
    capture_meta: dict[str, Any] | None,
    *,
    display: str | None = None,
) -> tuple[int, int, dict[str, Any]]:
    """Translate OCR/template pixel coords into desktop space for ydotool."""
    from ..control.screenshot_verify import enrich_screencast_stream_meta

    meta = enrich_screencast_stream_meta(dict(capture_meta or {}))
    png_w = int(meta.get("width") or 0)
    png_h = int(meta.get("height") or 0)
    region = meta.get("region") or {}

    if region:
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

    source = str(meta.get("source") or meta.get("monitor_name") or "")
    if source:
        monitor = _monitor_by_name(display, source)
        if monitor is not None:
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

    return local_x, local_y, {"mapping": "local"}


def _local_to_region_coords(
    local_x: int,
    local_y: int,
    *,
    png_w: int,
    png_h: int,
    region_w: int,
    region_h: int,
    rotation: str | None,
    allow_1to1_fallback: bool = False,
) -> tuple[int, int, float, float]:
    if png_w <= 0 or png_h <= 0:
        return local_x, local_y, 1.0, 1.0

    rot = rotation or "normal"
    if rot != "normal" and _aspect_mismatch(region_w, region_h, png_w, png_h):
        return _rotate_local_to_region(
            local_x, local_y, png_w=png_w, png_h=png_h, region_w=region_w, region_h=region_h, rotation=rot
        )

    scale_x = region_w / png_w if png_w > 0 else 1.0
    scale_y = region_h / png_h if png_h > 0 else 1.0
    if allow_1to1_fallback and rot == "normal" and _aspect_mismatch(region_w, region_h, png_w, png_h):
        scale_x = 1.0
        scale_y = 1.0
    return int(local_x * scale_x), int(local_y * scale_y), scale_x, scale_y


def _rotate_local_to_region(
    local_x: int,
    local_y: int,
    *,
    png_w: int,
    png_h: int,
    region_w: int,
    region_h: int,
    rotation: str,
) -> tuple[int, int, float, float]:
    """Map capture-local coords into monitor logical space when PNG orientation differs."""
    scale_x = region_w / png_h if png_h > 0 else 1.0
    scale_y = region_h / png_w if png_w > 0 else 1.0
    if rotation == "left":
        rel_x = int(local_y * scale_x)
        rel_y = int((png_w - local_x - 1) * scale_y)
    elif rotation == "right":
        rel_x = int((png_h - local_y - 1) * scale_x)
        rel_y = int(local_x * scale_y)
    elif rotation == "inverted":
        rel_x = int((png_w - local_x - 1) * scale_x)
        rel_y = int((png_h - local_y - 1) * scale_y)
    else:
        rel_x = int(local_x * (region_w / png_w if png_w > 0 else 1.0))
        rel_y = int(local_y * (region_h / png_h if png_h > 0 else 1.0))
        scale_x = region_w / png_w if png_w > 0 else 1.0
        scale_y = region_h / png_h if png_h > 0 else 1.0
    return rel_x, rel_y, scale_x, scale_y


def _aspect_mismatch(monitor_w: int, monitor_h: int, png_w: int, png_h: int) -> bool:
    if monitor_w <= 0 or monitor_h <= 0 or png_w <= 0 or png_h <= 0:
        return False
    monitor_ar = monitor_w / monitor_h
    png_ar = png_w / png_h
    return abs(monitor_ar - png_ar) > 0.35


def _rotation_for_monitor(display: str | None, name: str | None) -> str | None:
    if not name:
        return None
    monitor = _monitor_by_name(display, name)
    if monitor is None:
        return None
    return str(monitor.get("rotation") or "normal")


def _monitor_by_name(display: str | None, name: str) -> dict[str, Any] | None:
    from ..discovery import list_monitors, resolve_host_display

    resolved = resolve_host_display(display)
    for monitor in list_monitors(resolved):
        if str(monitor.get("name") or "") == name:
            return monitor
    return None
