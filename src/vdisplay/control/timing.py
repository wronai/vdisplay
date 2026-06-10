"""Shared delays for pointer focus and post-click settle before typing."""

from __future__ import annotations

import os


def control_focus_type_seconds() -> float:
    """Pause after click-to-focus before sending keystrokes (ms via env)."""
    raw = os.environ.get("VDISPLAY_CONTROL_FOCUS_MS", "350")
    try:
        return max(0.0, int(raw)) / 1000.0
    except ValueError:
        return 0.35


def control_pointer_settle_seconds() -> float:
    """Brief pause after pointer move/click so the compositor applies focus."""
    raw = os.environ.get("VDISPLAY_CONTROL_POINTER_SETTLE_MS", "50")
    try:
        return max(0.0, int(raw)) / 1000.0
    except ValueError:
        return 0.05
