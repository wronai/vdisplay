"""Parse physical monitor geometry from xrandr --listmonitors."""

from __future__ import annotations

import re

_GEOMETRY_MM_RE = re.compile(
    r"^(?P<width>\d+)/(?P<width_mm>\d+)x(?P<height>\d+)/(?P<height_mm>\d+)\+(?P<x>\d+)\+(?P<y>\d+)$"
)


def parse_geometry_mm(raw: str | None) -> dict[str, int | float]:
    """Parse xrandr --listmonitors geometry (px/mm + position)."""
    if not raw:
        return {}
    match = _GEOMETRY_MM_RE.match(str(raw).strip())
    if not match:
        return {}
    width_px = int(match.group("width"))
    height_px = int(match.group("height"))
    width_mm = int(match.group("width_mm"))
    height_mm = int(match.group("height_mm"))
    x = int(match.group("x"))
    y = int(match.group("y"))
    diag_mm = (width_mm**2 + height_mm**2) ** 0.5
    return {
        "width_px": width_px,
        "height_px": height_px,
        "width_mm": width_mm,
        "height_mm": height_mm,
        "geometry_x": x,
        "geometry_y": y,
        "diagonal_in": round(diag_mm / 25.4, 1),
    }
