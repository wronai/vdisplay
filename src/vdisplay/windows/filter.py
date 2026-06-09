from __future__ import annotations

from typing import Any

from .constants import JUNK_CLASS_MARKERS, JUNK_TITLES


def looks_like_internal_class(value: str) -> bool:
    lowered = (value or "").lower()
    return any(marker in lowered for marker in JUNK_CLASS_MARKERS)


def looks_like_internal_name(value: str) -> bool:
    lowered = (value or "").lower()
    return any(marker in lowered for marker in JUNK_CLASS_MARKERS)


def is_trivial_internal(*, window_id: str, root_id: str, role: str, width: int, height: int) -> bool:
    if window_id == root_id or role == "root":
        return True
    if role == "helper":
        return True
    return width <= 1 or height <= 1


def is_junk_title(title: str, net_wm_name: str) -> bool:
    lowered_title = (title or "").lower()
    lowered_name = (net_wm_name or "").lower()
    if lowered_title in JUNK_TITLES or lowered_name in JUNK_TITLES:
        return True
    return "mutter guard" in lowered_title or "focusproxy" in lowered_name


def is_visible_app(role: str, title: str, net_wm_name: str, width: int, height: int) -> bool:
    if role == "frame" and (title or net_wm_name):
        return True
    if role == "frame":
        return False
    return role == "application" and bool(title or net_wm_name) and width >= 200 and height >= 200


def is_internal_window(
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
    if is_trivial_internal(window_id=window_id, root_id=root_id, role=role, width=width, height=height):
        return True
    if is_junk_title(title, net_wm_name):
        return True
    if looks_like_internal_class(wm_class) or looks_like_internal_class(wm_instance):
        return True
    if looks_like_internal_name(net_wm_name or title):
        return True
    if process_name in {"mutter-x11-frames"} and role != "frame":
        return True
    if is_visible_app(role, title, net_wm_name, width, height):
        return False
    if role == "client" and (width < 80 or height < 80):
        return True
    return role == "client"


def matches_title(info: dict[str, Any], needle: str) -> bool:
    n = needle.lower()
    for field in ("title", "name", "app_label", "net_wm_name", "wm_class", "wm_class_instance", "process_name"):
        val = str(info.get(field) or "").lower()
        if n in val:
            return True
    return False


def matches_class(info: dict[str, Any], needle: str) -> bool:
    n = needle.lower()
    for field in ("wm_class", "wm_class_instance"):
        val = str(info.get(field) or "").lower()
        if n in val or val in n:
            return True
    return False


def matches_app(info: dict[str, Any], needle: str) -> bool:
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


def window_passes_filters(
    info: dict[str, Any],
    *,
    apps_only: bool,
    min_width: int,
    min_height: int,
    match_class: str | None,
    match_pid: int | None,
    match_app: str | None,
) -> bool:
    if apps_only and info.get("is_internal"):
        return False
    if info.get("width", 0) < min_width or info.get("height", 0) < min_height:
        return False
    if match_pid is not None and info.get("pid") != match_pid:
        return False
    if match_class and not matches_class(info, match_class):
        return False
    if match_app and not matches_app(info, match_app):
        return False
    return True


def filter_windows(
    windows: list[dict[str, Any]],
    *,
    match_title: str | None,
    match_class: str | None,
    match_pid: int | None,
    match_app: str | None,
) -> list[dict[str, Any]]:
    has_match = bool(match_title or match_class or match_pid or match_app)
    matches: list[dict[str, Any]] = []
    for info in windows:
        if match_pid is not None and info.get("pid") != match_pid:
            continue
        if match_class and not matches_class(info, match_class):
            continue
        if match_app and not matches_app(info, match_app):
            continue
        if match_title and not matches_title(info, match_title):
            continue
        if has_match:
            matches.append(info)
    return matches


def is_companion_frame(
    candidate: dict[str, Any],
    window: dict[str, Any],
    *,
    label: str,
    title: str,
) -> bool:
    if candidate.get("window_id") == window.get("window_id"):
        return False
    if candidate.get("type") != "frame":
        return False
    cand_label = str(candidate.get("app_label") or "").lower()
    cand_title = str(candidate.get("title") or candidate.get("name") or "").lower()
    if label and cand_label == label:
        return True
    return bool(title and cand_title == title)
