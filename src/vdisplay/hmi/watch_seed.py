"""Mouse seeding for evdev-relative tracking in HMI watch."""

from __future__ import annotations

from .mouse import MouseWatcher
from .pointer import is_wayland_session, pointer_probe_errors, probe_absolute_pointer


def seed_mouse_watcher(
    mouse_watcher: MouseWatcher,
    *,
    display: str | None,
    seed_xy: tuple[int, int] | None,
) -> list[str]:
    warnings: list[str] = []
    if seed_xy is not None:
        mouse_watcher.seed(*seed_xy)
        return warnings

    absolute = probe_absolute_pointer(display=display, use_gtk=True)
    if absolute is not None:
        source, xy = absolute
        mouse_watcher.seed(*xy)
        warnings.append(f"seeded evdev from {source}=({xy[0]},{xy[1]})")
        return warnings

    if is_wayland_session():
        warnings.append(
            "absolute pointer seed failed (gnome/gtk unavailable) — move mouse to start evdev-rel tracking"
        )
        errors = pointer_probe_errors()
        detail = "; ".join(f"{k}={v}" for k, v in errors.items() if v)
        if detail:
            warnings.append(detail)
    return warnings
