"""Window listing for the broker."""

from __future__ import annotations

from typing import Any

from vdisplay.application.services import discovery


def list_windows(**filters: Any) -> dict[str, Any]:
    display = filters.get("display")
    include_all = str(filters.get("include_all", "true")).lower() not in {"0", "false", "no"}
    apps_only_raw = filters.get("apps_only")
    apps_only = None
    if apps_only_raw is not None:
        apps_only = str(apps_only_raw).lower() in {"1", "true", "yes"}
    match_pid = filters.get("match_pid")
    if match_pid is not None and str(match_pid).strip():
        match_pid = int(match_pid)
    else:
        match_pid = None
    return discovery.list_windows_local(
        display,
        include_all=include_all,
        apps_only=apps_only,
        min_width=int(filters.get("min_width") or 0),
        min_height=int(filters.get("min_height") or 0),
        match_class=filters.get("match_class") or filters.get("wm_class"),
        match_pid=match_pid,
        match_app=filters.get("match_app") or filters.get("app"),
    )
