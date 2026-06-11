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
    if preferred and _display_socket_exists(preferred):
        # Explicitly requested virtual display (e.g. --display :99) that is
        # actually live — honor it instead of falling back to the host display.
        return preferred

    env_display = os.environ.get("DISPLAY")
    if env_display and not _looks_like_xvfb_only(env_display):
        return env_display

    for candidate in (":0", ":1"):
        if Path(f"/tmp/.X11-unix/X{candidate.lstrip(':')}").exists():
            return candidate
    return preferred or env_display or ":0"


def _display_socket_exists(display: str) -> bool:
    suffix = display.lstrip(":").split(".")[0]
    if not suffix.isdigit():
        return False
    return Path(f"/tmp/.X11-unix/X{suffix}").exists()


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

from .monitor_geometry import parse_geometry_mm as _parse_geometry_mm
def list_outputs(
    display: str | None = None,
    *,
    enrich_nl: bool = True,
    apps_only: bool = False,
) -> list[dict[str, str | bool | int | None]]:
    """List connected monitors (xrandr outputs). Alias: list_monitors()."""
    if shutil.which("xrandr") is None:
        raise BackendNotAvailableError("xrandr is not installed")

    display = resolve_host_display(display)
    query_meta = _parse_xrandr_query(display)
    if query_meta.get("_error"):
        raise VDisplayError(query_meta["_error"])

    monitors = _list_monitors(display)
    if monitors:
        outputs = _merge_output_metadata(monitors, query_meta)
    else:
        outputs = []
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
        outputs.sort(
            key=lambda o: (o.get("monitor_index") is None, o.get("monitor_index") or 0, str(o.get("name")))
        )

    from .nl import ensure_monitor_ids

    outputs = ensure_monitor_ids(outputs)
    if enrich_nl:
        return _attach_output_nl(display, outputs, apps_only=apps_only)
    return outputs


def _attach_output_nl(
    display: str,
    outputs: list[dict[str, str | bool | int | None]],
    *,
    apps_only: bool = False,
) -> list[dict[str, str | bool | int | None]]:
    from .nl import assign_windows_to_monitors, enrich_outputs_nl
    from .windows import list_windows_enriched

    try:
        windows = list_windows_enriched(display, only_visible=True, apps_only=apps_only)
    except Exception:
        windows = []
    windows = assign_windows_to_monitors(windows, outputs)
    return enrich_outputs_nl(outputs, windows)


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
                + ". Try: unset DISPLAY && vdisplay monitors"
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
        item.update(_parse_geometry_mm(str(monitor.get("geometry") or "")))
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
    from .nl import assign_windows_to_monitors
    from .windows import list_windows_enriched

    display = resolve_host_display(display)
    monitors: list[dict] = []
    try:
        monitors = list_outputs(display, enrich_nl=False)
    except Exception:
        monitors = []
    windows = list_windows_enriched(
        display,
        only_visible=only_visible,
        apps_only=apps_only,
        min_width=min_width,
        min_height=min_height,
        match_class=match_class,
        match_pid=match_pid,
        match_app=match_app,
    )
    return assign_windows_to_monitors(windows, monitors)


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
    try:
        from .capture.providers.engine import list_capture_providers

        payload["capture_providers"] = list_capture_providers(resolved)
    except Exception as exc:
        payload["capture_providers_error"] = str(exc)
    from .capture.linux_xwd import _is_wayland_session

    if _is_wayland_session():
        payload["session_type"] = "wayland"
        payload["host_capture_hint"] = (
            "vdisplay agent serve → vdisplay agent screencast start → vdisplay screenshot"
        )
        try:
            from .agent_config import resolve_agent_url
            from .client import AgentClient

            url = resolve_agent_url(allow_auto=True)
            if url:
                sc = AgentClient(url).screencast_status()
                payload["agent_url"] = url
                payload["screencast_ready"] = bool(sc.get("active") and sc.get("ready"))
                if not payload["screencast_ready"]:
                    payload["host_capture_hint"] += " (screencast not ready)"
            else:
                payload["screencast_ready"] = False
                payload["host_capture_hint"] += " (agent not running)"
        except Exception:
            payload["screencast_ready"] = False
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
            "check GNOME Displays or run: vdisplay monitors"
        )
    return None


def list_monitors(display: str | None = None) -> list[dict[str, str | bool | int | None]]:
    """Alias for list_outputs()."""
    return list_outputs(display)


def window_discovery_meta(display: str) -> dict[str, str]:
    session_type = os.environ.get("XDG_SESSION_TYPE", "unknown")
    meta: dict[str, str] = {
        "session_type": session_type,
        "window_source": "x11",
    }
    if session_type == "wayland":
        meta["hint"] = (
            f"Session is Wayland. vdisplay lists X11/XWayland windows on {display} via xdotool. "
            "Native Wayland apps (Firefox, Cursor, GNOME Terminal, etc.) are not visible here — "
            "only XWayland clients. Use `vdisplay windows --apps-only` for application windows only."
        )
    return meta

