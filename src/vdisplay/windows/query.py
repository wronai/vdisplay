from __future__ import annotations

from typing import Any

from ..nl import describe_window_nl
from ..utils import require_command
from .filter import (
    filter_windows,
    is_companion_frame,
    is_internal_window,
    window_passes_filters,
)
from .normalize import (
    derive_app_label,
    derive_role,
    normalize_atom_list,
    parse_wm_class,
    process_info,
    resolve_window_pid,
)
from .rank import dedupe_app_windows, pick_largest, window_sort_key
from .scan import root_window_id, search_window_ids, window_geometry, xdotool, xprop


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
    root_id = root_window_id(display)
    windows = scan_windows(
        display,
        root_id=root_id,
        only_visible=only_visible,
        apps_only=apps_only,
        min_width=min_width,
        min_height=min_height,
        match_class=match_class,
        match_pid=match_pid,
        match_app=match_app,
    )
    if apps_only:
        windows = dedupe_app_windows(windows)
    windows.sort(key=window_sort_key, reverse=True)
    return windows


def scan_windows(
    display: str,
    *,
    root_id: str,
    only_visible: bool,
    apps_only: bool,
    min_width: int,
    min_height: int,
    match_class: str | None,
    match_pid: int | None,
    match_app: str | None,
) -> list[dict[str, Any]]:
    windows: list[dict[str, Any]] = []
    for wid in search_window_ids(display, only_visible=only_visible):
        try:
            info = inspect_window(display, wid, root_id=root_id)
        except Exception:
            continue
        if not window_passes_filters(
            info,
            apps_only=apps_only,
            min_width=min_width,
            min_height=min_height,
            match_class=match_class,
            match_pid=match_pid,
            match_app=match_app,
        ):
            continue
        windows.append(info)
    return windows


def inspect_window(display: str, window_id: str, *, root_id: str | None = None) -> dict[str, Any]:
    root_id = root_id or root_window_id(display)
    props = xprop(display, window_id)

    title = xdotool(display, "getwindowname", window_id).strip()
    wm_name = props.get("WM_NAME", "")
    net_wm_name = props.get("_NET_WM_NAME", "")
    wm_instance, wm_class = parse_wm_class(props.get("WM_CLASS", ""))
    window_type = normalize_atom_list(props.get("_NET_WM_WINDOW_TYPE", ""))
    pid = resolve_window_pid(display, window_id, props)
    process = process_info(pid)

    geometry = window_geometry(display, window_id)
    width = geometry["width"]
    height = geometry["height"]

    app_label = derive_app_label(
        title=title,
        net_wm_name=net_wm_name,
        wm_name=wm_name,
        wm_instance=wm_instance,
        wm_class=wm_class,
        process_name=process.get("name"),
    )
    role = derive_role(
        window_id=window_id,
        root_id=root_id,
        wm_class=wm_class,
        width=width,
        height=height,
        title=title,
        net_wm_name=net_wm_name,
    )
    is_internal = is_internal_window(
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
    has_match = bool(match_title or match_class or match_pid or match_app)
    windows = list_windows_enriched(display, only_visible=True, apps_only=apps_only)
    matches = filter_windows(
        windows,
        match_title=match_title,
        match_class=match_class,
        match_pid=match_pid,
        match_app=match_app,
    )
    if matches or not has_match:
        return matches

    fallback = list_windows_enriched(display, only_visible=True, apps_only=False)
    return filter_windows(
        fallback,
        match_title=match_title,
        match_class=match_class,
        match_pid=match_pid,
        match_app=match_app,
    )


def pick_best_window(matches: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not matches:
        return None
    app_windows = [w for w in matches if not w.get("is_internal")]
    pool = app_windows or matches
    frames = [w for w in pool if w.get("type") == "frame"]
    if frames:
        pool = frames
    return pick_largest(pool)


def find_companion_frames(display: str, window: dict[str, Any]) -> list[dict[str, Any]]:
    label = str(window.get("app_label") or "").lower()
    title = str(window.get("title") or window.get("name") or "").lower()
    if not label and not title:
        return []

    companions: list[dict[str, Any]] = []
    for candidate in list_windows_enriched(display, only_visible=True, apps_only=False):
        if is_companion_frame(candidate, window, label=label, title=title):
            companions.append(candidate)
    return companions
