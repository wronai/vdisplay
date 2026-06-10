"""Execute CommandRequest via agent or local application services."""

from __future__ import annotations

import os
import time
from typing import Any

from .commands import CommandRequest, CommandResult, CommandVerb
from .errors import error_from_exception
from .handlers import execute_agent, execute_local
from .runtime import ExecutionPolicy, Route, get_execution_policy
from .session_recorder import extract_diagnostics, record_execution, session_recording_enabled
from .session_context import agent_audit_delegated, ensure_audit_session_dir, enrich_command_request
from .artifacts import build_artifacts
from .event_store import append_event, event_store_enabled, resolve_event_session_root
from .events import command_completed, command_received
from ..exceptions import VDisplayError


def _audit_record_on_client(route: Route) -> bool:
    return not (route == "agent" and session_recording_enabled() and agent_audit_delegated())


def _emit_command_received(cmd: CommandRequest, *, route: Route) -> None:
    session_root = resolve_event_session_root(cmd)
    if session_root is None:
        return
    append_event(session_root, command_received(cmd, route=route))


def _emit_command_completed(
    cmd: CommandRequest,
    result: CommandResult,
    *,
    route: Route,
    duration_ms: int,
) -> None:
    session_root = resolve_event_session_root(cmd)
    if session_root is None:
        return
    append_event(session_root, command_completed(cmd, result, route=route, duration_ms=duration_ms))


def _maybe_enrich_screenshot(cmd: CommandRequest, data: dict[str, Any]) -> dict[str, Any]:
    if cmd.verb != CommandVerb.SCREENSHOT:
        return data
    if cmd.extra.get("skip_img2nl"):
        return data
    from .services import img2nl_enrich

    return img2nl_enrich.enrich_screenshot_payload(data)


def execute(
    cmd: CommandRequest,
    *,
    policy: ExecutionPolicy | None = None,
    force_route: Route | None = None,
) -> CommandResult:
    """Single entry for command execution across CLI, DSL, REST, and agent dispatch."""
    cmd = enrich_command_request(cmd)
    ensure_audit_session_dir(cmd)
    pol = policy or get_execution_policy()
    route = force_route or pol.route(cmd)
    meta = pol.meta_for(route)
    started = time.perf_counter()
    if _audit_record_on_client(route):
        _emit_command_received(cmd, route=route)
    try:
        data = execute_agent(cmd) if route == "agent" else execute_local(cmd)
        data = _maybe_enrich_screenshot(cmd, data)
        result = CommandResult.success(
            action=cmd.action,
            data=data,
            command=cmd.line,
            meta=meta,
            artifacts=build_artifacts(cmd, data),
        )
    except VDisplayError as exc:
        result = CommandResult.failure(
            action=cmd.action,
            error=error_from_exception(exc),
            command=cmd.line,
            meta=meta,
        )
    except Exception as exc:
        result = CommandResult.failure(
            action=cmd.action,
            error=error_from_exception(exc),
            command=cmd.line,
            meta=meta,
        )
    result.diagnostics = extract_diagnostics(result)
    duration_ms = int((time.perf_counter() - started) * 1000)
    delegate_to_broker = route == "agent" and session_recording_enabled() and agent_audit_delegated()
    if delegate_to_broker:
        session_dir = os.environ.get("VDISPLAY_SESSION_DIR", "").strip()
        if session_dir and result.meta is not None:
            result.meta["session_dir"] = session_dir
            result.meta["audit_delegated"] = "broker"
        result.session_id = cmd.session_id
        result.request_id = cmd.request_id
    else:
        if _audit_record_on_client(route):
            _emit_command_completed(cmd, result, route=route, duration_ms=duration_ms)
        record_execution(cmd, result, route=route, duration_ms=duration_ms)
    return result
