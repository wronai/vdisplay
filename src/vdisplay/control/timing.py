"""Shared delays for pointer focus and post-click settle before typing."""

from __future__ import annotations

from ..application.env_defaults import env_int_value


def control_focus_type_seconds() -> float:
    """Pause after click-to-focus before sending keystrokes (ms via env)."""
    return max(0.0, env_int_value("VDISPLAY_CONTROL_FOCUS_MS", default=350)) / 1000.0


def control_pointer_settle_seconds() -> float:
    """Brief pause after pointer move/click so the compositor applies focus."""
    return max(0.0, env_int_value("VDISPLAY_CONTROL_POINTER_SETTLE_MS", default=50)) / 1000.0
