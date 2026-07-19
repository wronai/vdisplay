"""Backward-compatible re-exports — prefer ``vdisplay.capture.coordinate_map``."""

from __future__ import annotations

from typing import Any

from ..discovery import list_monitors, resolve_host_display


def monitor_by_name(display: str | None, name: str) -> dict[str, Any] | None:
    """Resolve public monitor metadata by output name."""
    resolved = resolve_host_display(display)
    for monitor in list_monitors(resolved):
        if str(monitor.get("name") or "") == name:
            return monitor
    return None


def _monitor_by_name(display: str | None, name: str) -> dict[str, Any] | None:
    """Backward-compatible private alias for pre-public-API consumers."""
    return monitor_by_name(display, name)


from ..capture.coordinate_map import (  # noqa: E402
    global_point_to_capture_local,
    global_pointer_coords,
    global_region_to_capture_local,
)

__all__ = [
    "_monitor_by_name",
    "global_pointer_coords",
    "global_point_to_capture_local",
    "global_region_to_capture_local",
    "monitor_by_name",
]
