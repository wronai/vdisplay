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
) -> dict[str, Any]:
    """List windows; agent path unless local_only (broker process)."""
    if local_only:
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
    return {
        "requested_display": display or os.environ.get("DISPLAY"),
        "resolved_display": resolved,
        "window_count": len(windows),
        **window_discovery_meta(resolved),
        "windows": windows,
    }


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
