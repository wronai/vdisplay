"""Monitor and window context for HMI watch (separate from evdev-rel coords)."""

from __future__ import annotations

import time
from typing import Any

from ..discovery import resolve_host_display
from ..utils import require_command
from ..windows.query import inspect_window, list_windows_enriched


def pick_context_coordinates(
    sources: dict[str, tuple[int, int]],
    *,
    stale_sources: tuple[str, ...],
    primary: str | None,
) -> tuple[int, int, str] | None:
    """Best-effort absolute coords for monitor/window lookup."""
    from .pointer import _trustworthy_absolute

    order = ("gnome", "gtk", "evdev", "xdotool")
    for name in order:
        if name not in sources or name in stale_sources:
            continue
        xy = sources[name]
        if not _trustworthy_absolute(name, xy):
            continue
        x, y = xy
        return x, y, name
    if "xdotool" in sources:
        x, y = sources["xdotool"]
        return x, y, "xdotool*"
    if primary == "evdev" and "evdev" in sources:
        x, y = sources["evdev"]
        return x, y, "evdev"
    return None


def _point_in_window(window: dict[str, Any], x: int, y: int) -> bool:
    left = int(window.get("x") or 0)
    top = int(window.get("y") or 0)
    width = int(window.get("width") or 0)
    height = int(window.get("height") or 0)
    if width <= 0 or height <= 0:
        return False
    return left <= x < left + width and top <= y < top + height


class WindowContextResolver:
    """Resolve window/app under pointer with short-lived window list cache."""

    def __init__(self, *, display: str | None = None, ttl: float = 2.0) -> None:
        self._display = resolve_host_display(display)
        self._ttl = max(0.5, float(ttl))
        self._windows: list[dict[str, Any]] = []
        self._windows_at = 0.0
        self._by_id: dict[str, dict[str, Any]] = {}

    def resolve(self, x: int, y: int, window_id: str | None) -> dict[str, Any] | None:
        if window_id:
            info = self._window_by_id(window_id)
            if info is not None:
                return info

        app_windows = [
            window
            for window in self._windows_cached()
            if _point_in_window(window, x, y) and not window.get("is_internal")
        ]
        if app_windows:
            return min(
                app_windows,
                key=lambda window: int(window.get("width") or 0) * int(window.get("height") or 0),
            )

        candidates = [window for window in self._windows_cached() if _point_in_window(window, x, y)]
        if not candidates:
            return None
        return min(
            candidates,
            key=lambda window: int(window.get("width") or 0) * int(window.get("height") or 0),
        )

    def _windows_cached(self) -> list[dict[str, Any]]:
        now = time.monotonic()
        if self._windows and now - self._windows_at < self._ttl:
            return self._windows
        try:
            require_command("xdotool")
            self._windows = list_windows_enriched(self._display, only_visible=True, apps_only=False)
        except Exception:
            self._windows = []
        self._windows_at = now
        return self._windows

    def _window_by_id(self, window_id: str) -> dict[str, Any] | None:
        cached = self._by_id.get(window_id)
        if cached is not None:
            return cached
        try:
            info = inspect_window(self._display, window_id)
        except Exception:
            return None
        self._by_id[window_id] = info
        return info
