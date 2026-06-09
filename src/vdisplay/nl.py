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
    process_part = f", process {process}" if process else ""
    class_part = f", class {wm_class}" if wm_class else ""
    internal = " internal helper" if info.get("is_internal") else ""

    return (
        f"{label} {role} window ({size}{position})"
        f"{process_part}{class_part}{internal}."
    ).replace("  ", " ")


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

    labels: list[str] = []
    for window in windows:
        label = window.get("app_label") or window.get("title") or window.get("name")
        if label and label not in labels:
            labels.append(str(label))

    if not labels:
        return f"{base}. Visible windows present but without readable app labels."

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


def enrich_outputs_nl(
    outputs: list[dict[str, Any]],
    windows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    for output in outputs:
        on_output = [w for w in windows if window_center_on_output(w, output)]
        output["nl"] = describe_output_nl(output, on_output)
    return outputs
