from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

from .exceptions import BackendNotAvailableError, VDisplayError
from .utils import require_command, run_command


def resolve_host_display(preferred: str | None = None) -> str:
    """Pick a real host X11 display, avoiding stale Xvfb :99 from prior sessions."""
    if preferred and not _looks_like_xvfb_only(preferred):
        return preferred

    env_display = os.environ.get("DISPLAY")
    if env_display and not _looks_like_xvfb_only(env_display):
        return env_display

    for candidate in (":0", ":1"):
        if Path(f"/tmp/.X11-unix/X{candidate.lstrip(':')}").exists():
            return candidate
    return preferred or env_display or ":0"


def _looks_like_xvfb_only(display: str) -> bool:
    if not display.startswith(":"):
        return False
    if display in {":0", ":1"}:
        return False
    # :99, :198, etc. — often Xvfb from vdisplay virtual tests
    suffix = display.lstrip(":")
    return suffix.isdigit() and int(suffix) >= 10


_ROTATION_DEGREES = {
    "normal": 0,
    "left": 90,
    "inverted": 180,
    "right": 270,
}


def list_outputs(display: str | None = None) -> list[dict[str, str | bool | int | None]]:
    if shutil.which("xrandr") is None:
        raise BackendNotAvailableError("xrandr is not installed")

    display = resolve_host_display(display)
    query_meta = _parse_xrandr_query(display)
    if query_meta.get("_error"):
        raise VDisplayError(query_meta["_error"])

    monitors = _list_monitors(display)
    if monitors:
        return _merge_output_metadata(monitors, query_meta)

    outputs: list[dict[str, str | bool | int | None]] = []
    for name, meta in query_meta.items():
        if name.startswith("_"):
            continue
        outputs.append(
            {
                "name": name,
                "connected": meta.get("connected", True),
                "primary": meta.get("primary", False),
                "geometry": meta.get("geometry"),
                "monitor_index": None,
                "label": name,
                "width": meta.get("width"),
                "height": meta.get("height"),
                "x": meta.get("x"),
                "y": meta.get("y"),
                "rotation": meta.get("rotation"),
                "rotation_degrees": meta.get("rotation_degrees"),
            }
        )
    outputs.sort(key=lambda o: (o.get("monitor_index") is None, o.get("monitor_index") or 0, str(o.get("name"))))
    return outputs


def _list_monitors(display: str) -> list[dict[str, str | bool | int | None]]:
    result = run_command(
        ["xrandr", "--listmonitors"],
        env={"DISPLAY": display},
        text=True,
        check=False,
    )
    if result.returncode != 0 or "Monitors:" not in result.stdout:
        return []

    monitors: list[dict[str, str | bool | int | None]] = []
    for line in result.stdout.splitlines():
        match = re.match(r"^\s*(\d+):\s+\+?\*?(\S+)\s+(\d+/\d+x\d+/\d+\+\d+\+\d+)\s+(\S+)", line)
        if not match:
            continue
        index, label, geometry, name = match.groups()
        monitors.append(
            {
                "name": name,
                "connected": True,
                "primary": "*" in line.split(":", 1)[1].split()[0] or label.startswith("*"),
                "geometry": geometry,
                "monitor_index": int(index),
                "label": label.lstrip("*"),
            }
        )
    return monitors


def _parse_xrandr_query(display: str) -> dict[str, dict[str, str | bool | int | None]]:
    result = run_command(
        ["xrandr", "--query"],
        env={"DISPLAY": display},
        text=True,
        check=False,
    )
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        return {
            "_error": (
                f"xrandr failed on DISPLAY={display}"
                + (f": {stderr}" if stderr else "")
                + ". Try: unset DISPLAY && vdisplay outputs"
            )
        }

    meta: dict[str, dict[str, str | bool | int | None]] = {}
    for line in result.stdout.splitlines():
        connected = re.match(
            r"^(\S+)\s+connected(?:\s+(primary))?\s+"
            r"(\d+)x(\d+)\+(\d+)\+(\d+)"
            r"(?:\s+(normal|left|inverted|right))?",
            line,
        )
        if connected:
            name, primary, width, height, xpos, ypos, rotation = connected.groups()
            rot = rotation or "normal"
            meta[name] = {
                "connected": True,
                "primary": primary is not None,
                "geometry": f"{width}x{height}+{xpos}+{ypos}",
                "width": int(width),
                "height": int(height),
                "x": int(xpos),
                "y": int(ypos),
                "rotation": rot,
                "rotation_degrees": _ROTATION_DEGREES.get(rot, 0),
            }
            continue

        disconnected = re.match(r"^(\S+)\s+disconnected", line)
        if disconnected:
            meta[disconnected.group(1)] = {
                "connected": False,
                "primary": False,
                "geometry": None,
                "width": None,
                "height": None,
                "x": None,
                "y": None,
                "rotation": None,
                "rotation_degrees": None,
            }
    return meta


def _merge_output_metadata(
    monitors: list[dict[str, str | bool | int | None]],
    query_meta: dict[str, dict[str, str | bool | int | None]],
) -> list[dict[str, str | bool | int | None]]:
    merged: list[dict[str, str | bool | int | None]] = []
    for monitor in monitors:
        name = str(monitor.get("name"))
        extra = query_meta.get(name, {})
        item = {
            **monitor,
            "geometry_mm": monitor.get("geometry"),
            "geometry_px": extra.get("geometry"),
            "geometry": extra.get("geometry") or monitor.get("geometry"),
            "width": extra.get("width"),
            "height": extra.get("height"),
            "x": extra.get("x"),
            "y": extra.get("y"),
            "rotation": extra.get("rotation"),
            "rotation_degrees": extra.get("rotation_degrees"),
            "connected": extra.get("connected", monitor.get("connected")),
            "primary": extra.get("primary", monitor.get("primary")),
        }
        merged.append(item)
    return merged


def list_windows(
    display: str | None = None,
    *,
    only_visible: bool = True,
    apps_only: bool = False,
    min_width: int = 0,
    min_height: int = 0,
    match_class: str | None = None,
    match_pid: int | None = None,
    match_app: str | None = None,
) -> list[dict]:
    from .windows import list_windows_enriched

    display = resolve_host_display(display)
    return list_windows_enriched(
        display,
        only_visible=only_visible,
        apps_only=apps_only,
        min_width=min_width,
        min_height=min_height,
        match_class=match_class,
        match_pid=match_pid,
        match_app=match_app,
    )


def find_window_suggestions(display: str, match_title: str, limit: int = 8) -> list[dict]:
    from .windows import find_windows

    if not match_title.strip():
        return []
    return find_windows(display, match_title=match_title, apps_only=True)[:limit]


def diagnose_display(display: str | None = None) -> dict:
    display = display or os.environ.get("DISPLAY", ":0")
    resolved = resolve_host_display(display)
    outputs: list[dict] = []
    outputs_error: str | None = None
    try:
        outputs = list_outputs(resolved)
    except VDisplayError as exc:
        outputs_error = str(exc)

    payload: dict = {
        "requested_display": display,
        "resolved_display": resolved,
        "display_overridden": display != resolved,
        "output_count": len(outputs),
        "outputs": outputs,
        "x11_socket": f"/tmp/.X11-unix/X{resolved.lstrip(':')}",
        "x11_socket_exists": Path(f"/tmp/.X11-unix/X{resolved.lstrip(':')}").exists(),
        "hint": _display_hint(display, resolved, outputs),
    }
    if outputs_error:
        payload["outputs_error"] = outputs_error
    return payload


def _display_hint(display: str, resolved: str, outputs: list[dict]) -> str | None:
    if _looks_like_xvfb_only(display):
        return (
            f"DISPLAY={display} looks like Xvfb; use host display {resolved} for mirror/relay. "
            "Run: unset DISPLAY or export DISPLAY=:0"
        )
    if len(outputs) < 2:
        return (
            "Only one X11 output visible. Mirror needs two outputs — "
            "check GNOME Displays or run: vdisplay outputs"
        )
    return None


