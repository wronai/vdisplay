"""Absolute pointer capture for calibration and desktop automation."""

from __future__ import annotations

from .pointer import is_wayland_session, probe_absolute_pointer, probe_xdotool


class PointerCaptureError(RuntimeError):
    """Raised when no live absolute pointer source is available."""


def capture_mouse_xy(*, display: str | None = None, use_gtk: bool = True) -> tuple[int, int, str]:
    """Return absolute desktop pointer coordinates and the probe source name."""
    best = probe_absolute_pointer(display=display, use_gtk=use_gtk)
    if best is not None:
        source, (x, y) = best
        return int(x), int(y), source

    xdotool = probe_xdotool(display=display)
    if xdotool is not None:
        tag = "xdotool*" if is_wayland_session() else "xdotool"
        return int(xdotool[0]), int(xdotool[1]), tag

    raise PointerCaptureError(
        "no absolute pointer source (Wayland: gnome/gtk unavailable; "
        "move mouse after seed or pass manual coords)"
    )
