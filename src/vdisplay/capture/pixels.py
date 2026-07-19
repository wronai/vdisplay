"""Dependency-free pixel primitives shared by capture adapters."""

from __future__ import annotations

import os


def resolve_capture_scale(
    override: float | None,
    *,
    env_var: str = "VDISPLAY_CAPTURE_SCALE",
    default: float = 0.2,
    minimum: float = 0.05,
    maximum: float = 1.0,
) -> float:
    """Resolve and clamp capture scale from an override or named environment input."""
    if override is not None:
        value = override
    else:
        raw = os.environ.get(env_var, str(default)).strip() or str(default)
        try:
            value = float(raw)
        except ValueError:
            value = default
    return max(minimum, min(maximum, value))


def downscale_rgb_nearest(
    rgb: bytes, src_w: int, src_h: int, dst_w: int, dst_h: int
) -> bytes:
    """Nearest-neighbor downscale of RGB triplet bytes."""
    if dst_w >= src_w and dst_h >= src_h:
        return rgb
    src_stride = src_w * 3
    cols = [(x * src_w // dst_w) * 3 for x in range(dst_w)]
    out = bytearray(dst_w * dst_h * 3)
    out_off = 0
    src_view = memoryview(rgb)
    for y in range(dst_h):
        row_base = (y * src_h // dst_h) * src_stride
        for col_off in cols:
            src_off = row_base + col_off
            out[out_off : out_off + 3] = src_view[src_off : src_off + 3]
            out_off += 3
    return bytes(out)


def rgb_mostly_black(rgb: bytes, *, threshold: float = 0.98) -> bool:
    """Return true when at least ``threshold`` of sampled RGB pixels are black."""
    if not rgb:
        return True
    step = max(1, (len(rgb) // 3) // 8000)
    black = 0
    total = 0
    for offset in range(0, len(rgb) - 2, 3 * step):
        total += 1
        if rgb[offset : offset + 3] == b"\x00\x00\x00":
            black += 1
    return total > 0 and (black / total) >= threshold


__all__ = ["downscale_rgb_nearest", "resolve_capture_scale", "rgb_mostly_black"]
