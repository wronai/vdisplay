"""Vision action bounds — expand narrow OCR hits for reliable click/type targets."""

from __future__ import annotations

from .models import ControlBounds


def action_bounds_for_vision(bounds: ControlBounds) -> ControlBounds:
    """Expand narrow OCR hits (e.g. placeholder fragments) into a wider input target."""
    if bounds.width >= 120:
        return bounds
    width = max(320, bounds.width * 4)
    return ControlBounds(
        x=bounds.x,
        y=max(0, bounds.y - 6),
        width=width,
        height=max(bounds.height + 12, 28),
    )


def click_point_for_vision(bounds: ControlBounds) -> tuple[int, int]:
    """Center of action bounds used for pointer injection."""
    action = action_bounds_for_vision(bounds)
    return action.center
