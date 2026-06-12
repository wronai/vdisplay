"""Discovery use-cases: monitors, windows, adopted state, diagnostics."""

from __future__ import annotations

import os
from typing import Any

from ...api import WindowRelaySession
from ...discovery import (
    diagnose_display,
    list_outputs,
    list_windows,
    resolve_host_display,
    window_discovery_meta,
)
from ...exceptions import VDisplayError
from ..commands import CommandRequest, CommandVerb
from ..runtime import resolve_apps_only


def _run_discovery(cmd: CommandRequest) -> dict[str, Any]:
    from ..executor import execute

    result = execute(cmd)
    if not result.ok:
        message = result.error.message if result.error else "discovery command failed"
        raise VDisplayError(message)
    return result.data


def list_monitors(display: str | None = None, *, include_all: bool = True) -> dict[str, Any]:
    return _run_discovery(
        CommandRequest(
            verb=CommandVerb.MONITORS,
            display=display,
            include_all=include_all,
        )
    )


def list_monitors_local(display: str | None = None, *, include_all: bool = True) -> dict[str, Any]:
    resolved = resolve_host_display(display)
    monitors = list_outputs(resolved, enrich_nl=True, apps_only=not include_all)
    return {
        "requested_display": display or os.environ.get("DISPLAY"),
        "resolved_display": resolved,
        "monitor_count": len(monitors),
        "monitors": monitors,
    }


def list_windows_payload(
    display: str | None = None,
    *,
    include_all: bool = True,
    apps_only: bool | None = None,
    include_internal: bool | None = None,
    min_width: int = 0,
    min_height: int = 0,
    match_class: str | None = None,
    match_pid: int | None = None,
    match_app: str | None = None,
    local_only: bool = False,
    correlate: bool = False,
) -> dict[str, Any]:
    """List windows; agent path unless local_only (broker process)."""
    if correlate or local_only:
        return list_windows_local(
            display,
            include_all=include_all,
            apps_only=apps_only,
            include_internal=include_internal,
            min_width=min_width,
            min_height=min_height,
            match_class=match_class,
            match_pid=match_pid,
            match_app=match_app,
            correlate=correlate,
        )
    apps_only = resolve_apps_only(
        include_all=include_all,
        apps_only=apps_only,
        include_internal=include_internal,
    )
    return _run_discovery(
        CommandRequest(
            verb=CommandVerb.WINDOWS,
            display=display,
            include_all=include_all,
            apps_only=apps_only,
            min_width=min_width,
            min_height=min_height,
            match_class=match_class,
            match_pid=match_pid,
            match_app=match_app,
        )
    )


def list_windows_local(
    display: str | None = None,
    *,
    include_all: bool = True,
    apps_only: bool | None = None,
    include_internal: bool | None = None,
    min_width: int = 0,
    min_height: int = 0,
    match_class: str | None = None,
    match_pid: int | None = None,
    match_app: str | None = None,
    correlate: bool = False,
) -> dict[str, Any]:
    resolved = resolve_host_display(display)
    apps_only = resolve_apps_only(
        include_all=include_all,
        apps_only=apps_only,
        include_internal=include_internal,
    )
    windows = list_windows(
        resolved,
        only_visible=True,
        apps_only=apps_only,
        min_width=min_width,
        min_height=min_height,
        match_class=match_class,
        match_pid=match_pid,
        match_app=match_app,
    )
    payload: dict[str, Any] = {
        "requested_display": display or os.environ.get("DISPLAY"),
        "resolved_display": resolved,
        "window_count": len(windows),
        **window_discovery_meta(resolved),
        "windows": windows,
    }
    if correlate:
        from ...windows.surface_registry import build_surface_registry

        registry = build_surface_registry(resolved, apps_only=apps_only)
        payload["correlated"] = True
        payload["surfaces"] = registry.get("surfaces") or []
        payload["surface_count"] = registry.get("surface_count", 0)
        payload["gnome_windows"] = registry.get("gnome_windows") or []
        payload["atspi_applications"] = registry.get("atspi_applications") or []
        payload["processes"] = registry.get("processes") or []
        payload["correlation_sources"] = registry.get("sources") or {}
        payload["gnome_window_count"] = registry.get("gnome_window_count", 0)
        payload["atspi_application_count"] = registry.get("atspi_application_count", 0)
        payload["correlation_process_count"] = registry.get("process_count", 0)
        payload["app_surfaces"] = registry.get("app_surfaces") or []
        payload["app_surface_count"] = registry.get("app_surface_count", 0)
        payload["jetbrains_awt_proxy_count"] = registry.get("jetbrains_awt_proxy_count", 0)
    return payload


def list_adopted(display: str | None = None) -> list[dict[str, Any]]:
    session = WindowRelaySession.create(display=display)
    session.start()
    try:
        return session.list_adopted()
    finally:
        session.stop()


def list_all(
    display: str | None = None,
    *,
    include_all: bool = True,
    apps_only: bool | None = None,
    include_internal: bool | None = None,
    match_class: str | None = None,
    match_pid: int | None = None,
    match_app: str | None = None,
) -> dict[str, Any]:
    if apps_only is None and include_internal is not None:
        include_all = include_internal
    elif apps_only is not None:
        include_all = not apps_only
    return _run_discovery(
        CommandRequest(
            verb=CommandVerb.ALL,
            display=display,
            include_all=include_all,
            match_class=match_class,
            match_pid=match_pid,
            match_app=match_app,
        )
    )


def list_all_local(
    display: str | None = None,
    *,
    include_all: bool = True,
    match_class: str | None = None,
    match_pid: int | None = None,
    match_app: str | None = None,
) -> dict[str, Any]:
    monitors = list_monitors_local(display, include_all=include_all)
    windows = list_windows_local(
        display,
        include_all=include_all,
        match_class=match_class,
        match_pid=match_pid,
        match_app=match_app,
    )
    adopted = list_adopted(display)
    return {
        "requested_display": monitors["requested_display"],
        "resolved_display": monitors["resolved_display"],
        "monitor_count": monitors["monitor_count"],
        "window_count": windows["window_count"],
        "adopted_count": len(adopted),
        "monitors": monitors["monitors"],
        "windows": windows["windows"],
        "adopted": adopted,
    }


def diagnose(display: str | None = None) -> dict[str, Any]:
    payload = diagnose_display(display)
    if "outputs" in payload:
        payload["monitors"] = payload.pop("outputs")
    return payload


def diagnose_unattended(display: str | None = None) -> dict[str, Any]:
    from ...agent_config import resolve_agent_url
    from ...capture.policy import assess_unattended_capture
    from ...control.descriptors import detect_platform_profile

    base = diagnose(display)
    url = resolve_agent_url(allow_auto=True)
    screencast_ready = base.get("screencast_ready")
    contract = assess_unattended_capture(
        display=display,
        agent_url=url,
        screencast_ready=screencast_ready if isinstance(screencast_ready, bool) else None,
    )
    platform = detect_platform_profile(display=display)
    return {
        **base,
        "host_environment": platform.host_environment.value,
        "unattended": contract.to_dict(),
        "sampler_hint": _sampler_hint(contract),
    }


def _sampler_hint(contract) -> str:
    if contract.recommended_mode == "strict":
        return "vdisplay sampler start --mode strict --vd-display :99 --interval 1"
    if contract.supports_unattended_capture:
        return (
            "vdisplay sampler start --mode desktop --interval 1 --source DP-2 "
            "--out-dir ./captures --progress"
        )
    return (
        "vdisplay agent serve && vdisplay agent screencast start && "
        "vdisplay sampler start --mode desktop --interval 1"
    )
