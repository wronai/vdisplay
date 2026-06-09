from __future__ import annotations

from typing import Any


def describe_window_nl(info: dict[str, Any]) -> str:
    """Natural-language summary of what a window contains."""
    label = (
        info.get("app_label")
        or info.get("title")
        or info.get("name")
        or f"window {info.get('window_id', '?')}"
    )
    role = str(info.get("type") or "window")
    width = info.get("width")
    height = info.get("height")
    x = info.get("x")
    y = info.get("y")
    process = info.get("process_name")
    wm_class = info.get("wm_class")

    size = f"{width}×{height}" if width and height else "unknown size"
    position = f" at ({x},{y})" if x is not None and y is not None else ""
    monitor_part = ""
    monitor_name = info.get("monitor_name")
    monitor_id = info.get("monitor_id")
    if monitor_name:
        monitor_part = f" on monitor {monitor_name}"
    elif monitor_id is not None:
        monitor_part = f" on monitor {monitor_id}"
    process_part = f", process {process}" if process else ""
    class_part = f", class {wm_class}" if wm_class else ""
    internal = " internal helper" if info.get("is_internal") else ""

    return (
        f"{label} {role} window ({size}{position})"
        f"{monitor_part}{process_part}{class_part}{internal}."
    ).replace("  ", " ")


def _user_visible_app_labels(windows: list[dict[str, Any]]) -> list[str]:
    labels: list[str] = []
    for window in windows:
        if window.get("is_internal"):
            continue
        if window.get("type") in {"root", "helper"}:
            continue
        label = window.get("app_label") or window.get("title") or window.get("name")
        if not label:
            continue
        text = str(label).strip()
        if text.lower() in {"(unknown)", ""}:
            continue
        if text not in labels:
            labels.append(text)
    return labels


def describe_output_nl(output: dict[str, Any], windows: list[dict[str, Any]]) -> str:
    """Natural-language summary of a monitor and visible windows on it."""
    name = str(output.get("name") or output.get("label") or "unknown")
    primary = "Primary " if output.get("primary") else ""
    width = output.get("width")
    height = output.get("height")
    rotation = output.get("rotation")
    rotation_degrees = output.get("rotation_degrees")

    size = f"{width}×{height}" if width and height else "unknown resolution"
    rotation_part = ""
    if rotation and rotation != "normal":
        degrees = f" ({rotation_degrees}°)" if rotation_degrees is not None else ""
        rotation_part = f", rotated {rotation}{degrees}"

    base = f"{primary}monitor {name} ({size}{rotation_part})"
    if not output.get("connected", True):
        return f"{base}. Disconnected."

    if not windows:
        return f"{base}. No visible application windows detected."

    labels = _user_visible_app_labels(windows)

    if not labels:
        return (
            f"{base}. No user application windows detected via X11 "
            "(internal/helper windows only, or native Wayland apps not listed)."
        )

    shown = ", ".join(labels[:8])
    extra = f" and {len(labels) - 8} more" if len(labels) > 8 else ""
    return f"{base}. Visible apps: {shown}{extra}."


def window_center_on_output(window: dict[str, Any], output: dict[str, Any]) -> bool:
    wx = window.get("x")
    wy = window.get("y")
    ww = window.get("width")
    wh = window.get("height")
    ox = output.get("x")
    oy = output.get("y")
    ow = output.get("width")
    oh = output.get("height")
    if None in (wx, wy, ww, wh, ox, oy, ow, oh):
        return False
    cx = int(wx) + int(ww) // 2
    cy = int(wy) + int(wh) // 2
    return int(ox) <= cx < int(ox) + int(ow) and int(oy) <= cy < int(oy) + int(oh)


def ensure_monitor_ids(monitors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for index, monitor in enumerate(monitors):
        if monitor.get("monitor_id") is not None:
            continue
        monitor_index = monitor.get("monitor_index")
        if monitor_index is not None:
            monitor["monitor_id"] = int(monitor_index)
        else:
            monitor["monitor_id"] = str(monitor.get("name") or index)
    return monitors


def find_monitor_for_window(
    window: dict[str, Any],
    monitors: list[dict[str, Any]],
) -> dict[str, Any] | None:
    for monitor in monitors:
        if window_center_on_output(window, monitor):
            return monitor
    return None


def assign_windows_to_monitors(
    windows: list[dict[str, Any]],
    monitors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    monitors = ensure_monitor_ids(monitors)
    for window in windows:
        monitor = find_monitor_for_window(window, monitors)
        if monitor:
            window["monitor_id"] = monitor.get("monitor_id")
            window["monitor_name"] = monitor.get("name")
            window["monitor_index"] = monitor.get("monitor_index")
        else:
            window["monitor_id"] = None
            window["monitor_name"] = None
            window["monitor_index"] = None
        window["nl"] = describe_window_nl(window)
    return windows


def enrich_outputs_nl(
    outputs: list[dict[str, Any]],
    windows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    for output in outputs:
        on_output = [w for w in windows if window_center_on_output(w, output)]
        output["nl"] = describe_output_nl(output, on_output)
    return outputs
