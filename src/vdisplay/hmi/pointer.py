"""Desktop pointer probes for live HMI watch — public re-exports."""

from __future__ import annotations

from ..discovery import list_monitors
from .pointer_probes import (
    is_wayland_session,
    monitor_at,
    pointer_probe_errors,
    probe_absolute_pointer,
    probe_all_sources,
    probe_gnome_shell_pointer,
    probe_gtk_subprocess,
    probe_xdotool,
    trustworthy_absolute as _trustworthy_absolute,
)
from .pointer_sampling import sample_pointer
from .pointer_types import PointerSample

__all__ = [
    "PointerSample",
    "list_monitors",
    "is_wayland_session",
    "monitor_at",
    "pointer_probe_errors",
    "probe_absolute_pointer",
    "probe_all_sources",
    "probe_gnome_shell_pointer",
    "probe_gtk_subprocess",
    "probe_xdotool",
    "sample_pointer",
    "_trustworthy_absolute",
]
