from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Any

from .exceptions import VDisplayError
from .nl import describe_window_nl
from .utils import require_command, run_command

_JUNK_TITLES = frozenset(
    {
        "",
        "mutter guard window",
        "focusproxy",
        "content window",
    }
)
_JUNK_CLASS_MARKERS = (
    "mutter guard",
    "focusproxy",
    "kotlinx-coroutines",
    "sun-awt-x11-xcanvaspeer",
    "javaawtcanvas",
    "gdk-toplevel",
)
_FRAME_CLASSES = frozenset({"mutter-x11-frames", "mutter"})


def list_windows_enriched(
    display: str,
    *,
    only_visible: bool = True,
    apps_only: bool = False,
    min_width: int = 0,
    min_height: int = 0,
    match_class: str | None = None,
    match_pid: int | None = None,
    match_app: str | None = None,
) -> list[dict[str, Any]]:
    require_command("xdotool")
    root_id = _root_window_id(display)

    args = ["xdotool", "search"]
    if only_visible:
        args.append("--onlyvisible")
    args.extend(["--name", ""])

    result = run_command(args, env={"DISPLAY": display}, text=True, check=False)
    windows: list[dict[str, Any]] = []
    for wid in result.stdout.splitlines():
        wid = wid.strip()
        if not wid:
            continue
        try:
            info = inspect_window(display, wid, root_id=root_id)
        except Exception:
            continue
        if apps_only and info.get("is_internal"):
            continue
        if info.get("width", 0) < min_width or info.get("height", 0) < min_height:
            continue
        if match_pid is not None and info.get("pid") != match_pid:
            continue
        if match_class and not _matches_class(info, match_class):
            continue
        if match_app and not _matches_app(info, match_app):
            continue
        windows.append(info)

    if apps_only:
        windows = _dedupe_app_windows(windows)
    windows.sort(key=_window_sort_key, reverse=True)
    return windows


def _dedupe_app_windows(windows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Prefer real application windows over mutter frame duplicates."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for window in windows:
        key = str(window.get("app_label") or window.get("title") or window.get("window_id")).lower()
        grouped.setdefault(key, []).append(window)

    deduped: list[dict[str, Any]] = []
    for group in grouped.values():
        real_apps = [
            w
            for w in group
            if w.get("type") == "application"
            and str(w.get("process_name") or "") not in {"mutter-x11-fram", "mutter-x11-frames"}
        ]
        frames = [w for w in group if w.get("type") == "frame"]
        if real_apps:
            deduped.append(max(real_apps, key=lambda w: (w.get("width", 0) or 0) * (w.get("height", 0) or 0)))
        elif len(frames) == 1:
            deduped.append(frames[0])
        elif group:
            deduped.append(max(group, key=lambda w: (w.get("width", 0) or 0) * (w.get("height", 0) or 0)))
    return deduped


def find_companion_frames(display: str, window: dict[str, Any]) -> list[dict[str, Any]]:
    label = str(window.get("app_label") or "").lower()
    title = str(window.get("title") or window.get("name") or "").lower()
    if not label and not title:
        return []

    companions: list[dict[str, Any]] = []
    for candidate in list_windows_enriched(display, only_visible=True, apps_only=False):
        if candidate.get("window_id") == window.get("window_id"):
            continue
        if candidate.get("type") != "frame":
            continue
        cand_label = str(candidate.get("app_label") or "").lower()
        cand_title = str(candidate.get("title") or candidate.get("name") or "").lower()
        if label and cand_label == label:
            companions.append(candidate)
        elif title and cand_title == title:
            companions.append(candidate)
    return companions


def inspect_window(display: str, window_id: str, *, root_id: str | None = None) -> dict[str, Any]:
    root_id = root_id or _root_window_id(display)
    props = _xprop(display, window_id)

    title = _xdotool(display, "getwindowname", window_id).strip()
    wm_name = props.get("WM_NAME", "")
    net_wm_name = props.get("_NET_WM_NAME", "")
    wm_class_raw = props.get("WM_CLASS", "")
    wm_instance, wm_class = _parse_wm_class(wm_class_raw)
    window_type = _normalize_atom_list(props.get("_NET_WM_WINDOW_TYPE", ""))
    pid = _resolve_window_pid(display, window_id, props)
    process = _process_info(pid)

    geometry = _window_geometry(display, window_id)
    width = geometry["width"]
    height = geometry["height"]

    app_label = _derive_app_label(
        title=title,
        net_wm_name=net_wm_name,
        wm_name=wm_name,
        wm_instance=wm_instance,
        wm_class=wm_class,
        process_name=process.get("name"),
    )
    role = _derive_role(
        window_id=window_id,
        root_id=root_id,
        wm_class=wm_class,
        width=width,
        height=height,
        title=title,
        net_wm_name=net_wm_name,
    )
    is_internal = _is_internal_window(
        window_id=window_id,
        root_id=root_id,
        role=role,
        wm_class=wm_class,
        wm_instance=wm_instance,
        title=title,
        net_wm_name=net_wm_name,
        width=width,
        height=height,
        pid=pid,
        process_name=process.get("name"),
    )

    info = {
        "window_id": window_id,
        "title": title or None,
        "name": net_wm_name or wm_name or title or None,
        "type": role,
        "wm_class": wm_class or None,
        "wm_class_instance": wm_instance or None,
        "window_type": window_type or None,
        "pid": pid,
        "process_name": process.get("name"),
        "process_cmdline": process.get("cmdline"),
        "app_label": app_label,
        "is_internal": is_internal,
        "x": geometry["x"],
        "y": geometry["y"],
        "width": width,
        "height": height,
        "display": display,
    }
    info["nl"] = describe_window_nl(info)
    return info


def find_windows(
    display: str,
    *,
    match_title: str | None = None,
    match_class: str | None = None,
    match_pid: int | None = None,
    match_app: str | None = None,
    apps_only: bool = True,
) -> list[dict[str, Any]]:
    windows = list_windows_enriched(display, only_visible=True, apps_only=apps_only)
    matches: list[dict[str, Any]] = []
    for info in windows:
        if match_pid is not None and info.get("pid") != match_pid:
            continue
        if match_class and not _matches_class(info, match_class):
            continue
        if match_app and not _matches_app(info, match_app):
            continue
        if match_title and not _matches_title(info, match_title):
            continue
        if match_title or match_class or match_pid or match_app:
            matches.append(info)
    if not matches and (match_title or match_class or match_pid or match_app):
        # fallback: search all windows including internal
        for info in list_windows_enriched(display, only_visible=True, apps_only=False):
            if match_pid is not None and info.get("pid") != match_pid:
                continue
            if match_class and not _matches_class(info, match_class):
                continue
            if match_app and not _matches_app(info, match_app):
                continue
            if match_title and not _matches_title(info, match_title):
                continue
            matches.append(info)
    return matches


def pick_best_window(matches: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not matches:
        return None
    app_windows = [w for w in matches if not w.get("is_internal")]
    pool = app_windows or matches
    frames = [w for w in pool if w.get("type") == "frame"]
    if frames:
        pool = frames
    return max(pool, key=lambda w: (w.get("width", 0) or 0) * (w.get("height", 0) or 0))


def _derive_app_label(
    *,
    title: str,
    net_wm_name: str,
    wm_name: str,
    wm_instance: str,
    wm_class: str,
    process_name: str | None,
) -> str:
    for candidate in (title, net_wm_name, wm_name):
        if candidate and candidate.lower() not in _JUNK_TITLES:
            cleaned = candidate.strip()
            if not _looks_like_internal_name(cleaned):
                return cleaned
    if process_name and process_name not in {"mutter-x11-frames", "xdg-desktop-portal-gnome"}:
        return process_name
    if wm_instance and not _looks_like_internal_class(wm_instance):
        return wm_instance
    if wm_class and wm_class not in _FRAME_CLASSES and not _looks_like_internal_class(wm_class):
        return wm_class
    return title or net_wm_name or wm_name or wm_class or "(unknown)"


def _derive_role(
    *,
    window_id: str,
    root_id: str,
    wm_class: str,
    width: int,
    height: int,
    title: str,
    net_wm_name: str,
) -> str:
    if window_id == root_id:
        return "root"
    if wm_class in _FRAME_CLASSES or "mutter-x11-frames" in wm_class:
        return "frame"
    if width <= 1 or height <= 1:
        return "helper"
    lowered = f"{title} {net_wm_name}".lower()
    if "guard" in lowered:
        return "helper"
    if _looks_like_internal_class(wm_class) or _looks_like_internal_name(net_wm_name or title):
        return "client"
    return "application"


def _is_internal_window(
    *,
    window_id: str,
    root_id: str,
    role: str,
    wm_class: str,
    wm_instance: str,
    title: str,
    net_wm_name: str,
    width: int,
    height: int,
    pid: int | None,
    process_name: str | None,
) -> bool:
    if window_id == root_id or role == "root":
        return True
    if role == "helper":
        return True
    if width <= 1 or height <= 1:
        return True
    lowered_title = (title or "").lower()
    lowered_name = (net_wm_name or "").lower()
    if lowered_title in _JUNK_TITLES or lowered_name in _JUNK_TITLES:
        return True
    if "mutter guard" in lowered_title or "focusproxy" in lowered_name:
        return True
    if _looks_like_internal_class(wm_class) or _looks_like_internal_class(wm_instance):
        return True
    if _looks_like_internal_name(net_wm_name or title):
        return True
    if process_name in {"mutter-x11-frames"} and role != "frame":
        return True
    # Keep framed app windows — title on mutter frame is user-visible.
    if role == "frame" and (title or net_wm_name):
        return False
    if role == "frame":
        return False
    if role == "application" and (title or net_wm_name) and width >= 200 and height >= 200:
        return False
    if role == "client" and (width < 80 or height < 80):
        return True
    return role == "client"


def _looks_like_internal_class(value: str) -> bool:
    lowered = (value or "").lower()
    return any(marker in lowered for marker in _JUNK_CLASS_MARKERS)


def _looks_like_internal_name(value: str) -> bool:
    lowered = (value or "").lower()
    return any(marker in lowered for marker in _JUNK_CLASS_MARKERS)


def _matches_title(info: dict[str, Any], needle: str) -> bool:
    n = needle.lower()
    for field in ("title", "name", "app_label", "net_wm_name", "wm_class", "wm_class_instance", "process_name"):
        val = str(info.get(field) or "").lower()
        if n in val:
            return True
    return False


def _matches_class(info: dict[str, Any], needle: str) -> bool:
    n = needle.lower()
    for field in ("wm_class", "wm_class_instance"):
        val = str(info.get(field) or "").lower()
        if n in val or val in n:
            return True
    return False


def _matches_app(info: dict[str, Any], needle: str) -> bool:
    n = needle.lower().strip()
    if not n:
        return False
    for field in (
        "app_label",
        "process_name",
        "title",
        "name",
        "wm_class",
        "wm_class_instance",
    ):
        val = str(info.get(field) or "").lower().strip()
        if not val:
            continue
        if n in val or val in n:
            return True
    return False


def _window_sort_key(info: dict[str, Any]) -> tuple[int, int, int]:
    internal = 1 if info.get("is_internal") else 0
    area = (info.get("width") or 0) * (info.get("height") or 0)
    frame_boost = 1 if info.get("type") == "frame" else 0
    return (frame_boost, -internal, area)


def _root_window_id(display: str) -> str:
    if shutil.which("xwininfo") is None:
        return ""
    result = run_command(["xwininfo", "-root"], env={"DISPLAY": display}, text=True, check=False)
    match = re.search(r"Window id:\s*(0x[0-9a-fA-F]+)", result.stdout)
    if not match:
        return ""
    return str(int(match.group(1), 16))


def _xdotool(display: str, *args: str) -> str:
    result = run_command(["xdotool", *args], env={"DISPLAY": display}, text=True, check=False)
    return result.stdout


def _xprop(display: str, window_id: str) -> dict[str, str]:
    if shutil.which("xprop") is None:
        return {}
    wid = _format_window_id(window_id)
    result = run_command(
        [
            "xprop",
            "-id",
            wid,
            "WM_CLASS",
            "WM_NAME",
            "_NET_WM_NAME",
            "_NET_WM_PID",
            "_NET_WM_WINDOW_TYPE",
        ],
        env={"DISPLAY": display},
        text=True,
        check=False,
    )
    props: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if "=" not in line:
            continue
        key, raw = line.split("=", 1)
        key = key.strip().split("(", 1)[0]
        raw = raw.strip()
        if raw.endswith(","):
            raw = raw[:-1].strip()
        props[key] = _decode_xprop_value(raw)
    return props


def _decode_xprop_value(raw: str) -> str:
    raw = raw.strip()
    if not raw or raw == '""':
        return ""
    parts = re.findall(r'"([^"]*)"', raw)
    if parts:
        return ", ".join(parts)
    if raw.startswith("(") and raw.endswith(")"):
        return raw[1:-1].strip()
    return raw


def _parse_wm_class(raw: str) -> tuple[str, str]:
    if not raw:
        return "", ""
    parts = re.findall(r'"([^"]*)"', raw)
    if not parts and "," in raw:
        parts = [p.strip() for p in raw.split(",", 1)]
    if len(parts) >= 2:
        return parts[0].strip(), parts[1].strip()
    if len(parts) == 1:
        return parts[0], parts[0]
    return raw.strip(), raw.strip()


def _normalize_atom_list(raw: str) -> str:
    if not raw:
        return ""
    atoms = re.findall(r"_NET_WM_WINDOW_TYPE_(\w+)", raw.upper())
    if atoms:
        return atoms[-1].lower()
    return raw.strip("() ").split("/")[-1].lower()


def _resolve_window_pid(display: str, window_id: str, props: dict[str, str]) -> int | None:
    pid_raw = props.get("_NET_WM_PID", "").strip()
    if pid_raw.isdigit():
        return int(pid_raw)
    result = run_command(
        ["xdotool", "getwindowpid", window_id],
        env={"DISPLAY": display},
        text=True,
        check=False,
    )
    out = result.stdout.strip()
    if out.isdigit():
        return int(out)
    return None


def _process_info(pid: int | None) -> dict[str, str | None]:
    if pid is None or pid <= 0:
        return {"name": None, "cmdline": None}
    comm = Path(f"/proc/{pid}/comm")
    cmdline = Path(f"/proc/{pid}/cmdline")
    name = comm.read_text(encoding="utf-8").strip() if comm.exists() else None
    cmd = None
    if cmdline.exists():
        raw = cmdline.read_bytes().replace(b"\x00", b" ").strip()
        cmd = raw.decode("utf-8", errors="replace")[:240] or None
    return {"name": name, "cmdline": cmd}


def _window_geometry(display: str, window_id: str) -> dict[str, int]:
    result = run_command(
        ["xdotool", "getwindowgeometry", "--shell", window_id],
        env={"DISPLAY": display},
        text=True,
        check=False,
    )
    values: dict[str, int] = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, raw = line.split("=", 1)
            if key in {"X", "Y", "WIDTH", "HEIGHT"}:
                values[key] = int(raw)
    return {
        "x": values.get("X", 0),
        "y": values.get("Y", 0),
        "width": values.get("WIDTH", 0),
        "height": values.get("HEIGHT", 0),
    }


def _format_window_id(window_id: str) -> str:
    if window_id.startswith("0x"):
        return window_id
    try:
        return hex(int(window_id))
    except ValueError:
        return window_id
