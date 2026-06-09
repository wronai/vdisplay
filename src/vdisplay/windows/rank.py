from __future__ import annotations

from typing import Any


def window_area(window: dict[str, Any]) -> int:
    return (window.get("width", 0) or 0) * (window.get("height", 0) or 0)


def pick_largest(windows: list[dict[str, Any]]) -> dict[str, Any]:
    return max(windows, key=window_area)


def pick_best_from_group(group: list[dict[str, Any]]) -> dict[str, Any]:
    real_apps = [
        w
        for w in group
        if w.get("type") == "application"
        and str(w.get("process_name") or "") not in {"mutter-x11-fram", "mutter-x11-frames"}
    ]
    if real_apps:
        return pick_largest(real_apps)
    frames = [w for w in group if w.get("type") == "frame"]
    if len(frames) == 1:
        return frames[0]
    return pick_largest(group)


def dedupe_app_windows(windows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Prefer real application windows over mutter frame duplicates."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for window in windows:
        key = str(window.get("app_label") or window.get("title") or window.get("window_id")).lower()
        grouped.setdefault(key, []).append(window)

    return [pick_best_from_group(group) for group in grouped.values()]


def window_sort_key(info: dict[str, Any]) -> tuple[int, int, int]:
    internal = 1 if info.get("is_internal") else 0
    area = (info.get("width") or 0) * (info.get("height") or 0)
    frame_boost = 1 if info.get("type") == "frame" else 0
    return (frame_boost, -internal, area)
