"""Rotation and aspect-ratio helpers for desktop ↔ PNG coordinate mapping."""

from __future__ import annotations


def aspect_mismatch(monitor_w: int, monitor_h: int, png_w: int, png_h: int) -> bool:
    if monitor_w <= 0 or monitor_h <= 0 or png_w <= 0 or png_h <= 0:
        return False
    monitor_ar = monitor_w / monitor_h
    png_ar = png_w / png_h
    return abs(monitor_ar - png_ar) > 0.35


def _forward_left(local_x: int, local_y: int, *, png_w: int, png_h: int, region_w: int, region_h: int) -> tuple[int, int, float, float]:
    scale_x = region_w / png_h if png_h > 0 else 1.0
    scale_y = region_h / png_w if png_w > 0 else 1.0
    return int(local_y * scale_x), int((png_w - local_x - 1) * scale_y), scale_x, scale_y


def _forward_right(local_x: int, local_y: int, *, png_w: int, png_h: int, region_w: int, region_h: int) -> tuple[int, int, float, float]:
    scale_x = region_w / png_h if png_h > 0 else 1.0
    scale_y = region_h / png_w if png_w > 0 else 1.0
    return int((png_h - local_y - 1) * scale_x), int(local_x * scale_y), scale_x, scale_y


def _forward_inverted(local_x: int, local_y: int, *, png_w: int, png_h: int, region_w: int, region_h: int) -> tuple[int, int, float, float]:
    scale_x = region_w / png_w if png_w > 0 else 1.0
    scale_y = region_h / png_h if png_h > 0 else 1.0
    return int((png_w - local_x - 1) * scale_x), int((png_h - local_y - 1) * scale_y), scale_x, scale_y


def _forward_normal(local_x: int, local_y: int, *, png_w: int, png_h: int, region_w: int, region_h: int) -> tuple[int, int, float, float]:
    scale_x = region_w / png_w if png_w > 0 else 1.0
    scale_y = region_h / png_h if png_h > 0 else 1.0
    return int(local_x * scale_x), int(local_y * scale_y), scale_x, scale_y


def rotate_local_to_region(
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
    if rotation == "left":
        return _forward_left(local_x, local_y, png_w=png_w, png_h=png_h, region_w=region_w, region_h=region_h)
    if rotation == "right":
        return _forward_right(local_x, local_y, png_w=png_w, png_h=png_h, region_w=region_w, region_h=region_h)
    if rotation == "inverted":
        return _forward_inverted(local_x, local_y, png_w=png_w, png_h=png_h, region_w=region_w, region_h=region_h)
    return _forward_normal(local_x, local_y, png_w=png_w, png_h=png_h, region_w=region_w, region_h=region_h)


def local_to_region_coords(
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
    if rot != "normal" and aspect_mismatch(region_w, region_h, png_w, png_h):
        return rotate_local_to_region(
            local_x, local_y, png_w=png_w, png_h=png_h, region_w=region_w, region_h=region_h, rotation=rot
        )

    scale_x = region_w / png_w if png_w > 0 else 1.0
    scale_y = region_h / png_h if png_h > 0 else 1.0
    if allow_1to1_fallback and rot == "normal" and aspect_mismatch(region_w, region_h, png_w, png_h):
        scale_x = 1.0
        scale_y = 1.0
    return int(local_x * scale_x), int(local_y * scale_y), scale_x, scale_y


def _inverse_left(rel_x: int, rel_y: int, *, png_w: int, png_h: int, region_w: int, region_h: int) -> tuple[int, int]:
    scale_x = region_w / png_h if png_h > 0 else 1.0
    scale_y = region_h / png_w if png_w > 0 else 1.0
    local_y = int(rel_x / scale_x) if scale_x else rel_x
    local_x = int(png_w - 1 - rel_y / scale_y) if scale_y else rel_y
    return local_x, local_y


def _inverse_right(rel_x: int, rel_y: int, *, png_w: int, png_h: int, region_w: int, region_h: int) -> tuple[int, int]:
    scale_x = region_w / png_h if png_h > 0 else 1.0
    scale_y = region_h / png_w if png_w > 0 else 1.0
    local_y = int(png_h - 1 - rel_x / scale_x) if scale_x else rel_x
    local_x = int(rel_y / scale_y) if scale_y else rel_y
    return local_x, local_y


def _inverse_inverted(rel_x: int, rel_y: int, *, png_w: int, png_h: int, region_w: int, region_h: int) -> tuple[int, int]:
    scale_x = region_w / png_w if png_w > 0 else 1.0
    scale_y = region_h / png_h if png_h > 0 else 1.0
    local_x = int(png_w - 1 - rel_x / scale_x) if scale_x else rel_x
    local_y = int(png_h - 1 - rel_y / scale_y) if scale_y else rel_y
    return local_x, local_y


def _inverse_normal(rel_x: int, rel_y: int, *, png_w: int, png_h: int, region_w: int, region_h: int) -> tuple[int, int]:
    scale_x = region_w / png_w if png_w > 0 else 1.0
    scale_y = region_h / png_h if png_h > 0 else 1.0
    local_x = int(rel_x / scale_x) if scale_x else rel_x
    local_y = int(rel_y / scale_y) if scale_y else rel_y
    return local_x, local_y


def region_rel_to_local(
    rel_x: int,
    rel_y: int,
    *,
    png_w: int,
    png_h: int,
    region_w: int,
    region_h: int,
    rotation: str | None,
) -> tuple[int, int]:
    """Inverse of ``local_to_region_coords`` for a single stream-relative point."""
    if png_w <= 0 or png_h <= 0:
        return rel_x, rel_y

    rot = rotation or "normal"
    if rot != "normal" and aspect_mismatch(region_w, region_h, png_w, png_h):
        if rot == "left":
            return _inverse_left(rel_x, rel_y, png_w=png_w, png_h=png_h, region_w=region_w, region_h=region_h)
        if rot == "right":
            return _inverse_right(rel_x, rel_y, png_w=png_w, png_h=png_h, region_w=region_w, region_h=region_h)
        return _inverse_inverted(rel_x, rel_y, png_w=png_w, png_h=png_h, region_w=region_w, region_h=region_h)

    return _inverse_normal(rel_x, rel_y, png_w=png_w, png_h=png_h, region_w=region_w, region_h=region_h)
