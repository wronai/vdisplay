"""Run broker requests through executor when audit headers are present."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from dataclasses import replace
from typing import Any

from fastapi.responses import JSONResponse
from vdisplay.application.commands import CommandRequest, CommandResult, CommandVerb
from vdisplay.application.executor import execute
from vdisplay.application.session_recorder import extract_diagnostics, record_execution

from ..audit_context import AuditContext, apply_audit_env
from ..envelope import from_runtime, json_error, json_from_runtime


async def execute_audit_route(
    action: str,
    verb: CommandVerb,
    body: dict[str, Any],
    *,
    audit: AuditContext,
    fallback: Callable[[dict[str, Any]], dict[str, Any]],
) -> JSONResponse:
    if not audit.should_record:
        try:
            payload = await asyncio.to_thread(fallback, body)
            return json_from_runtime(action, payload)
        except Exception as exc:
            return json_error(action, exc)

    with apply_audit_env(audit):
        cmd = CommandRequest.from_agent_body(verb, body, audit=audit)
        result = await asyncio.to_thread(execute, cmd, force_route="local")
        return _json_from_command_result(action, result)


async def execute_audited_service(
    action: str,
    body: dict[str, Any],
    *,
    audit: AuditContext,
    fallback: Callable[[dict[str, Any]], dict[str, Any]],
    record_verb: CommandVerb = CommandVerb.SCREENSHOT,
) -> JSONResponse:
    """Record audit steps for broker-only services (capture/frame, relay, etc.)."""
    if not audit.should_record:
        try:
            payload = await asyncio.to_thread(fallback, body)
            return json_from_runtime(action, payload)
        except Exception as exc:
            return json_error(action, exc)

    with apply_audit_env(audit):
        cmd = CommandRequest.from_agent_body(record_verb, body, audit=audit)
        cmd = replace(cmd, extra={**cmd.extra, "agent_action": action})
        started = time.perf_counter()
        try:
            data = await asyncio.to_thread(fallback, body)
            if not isinstance(data, dict):
                data = {"payload": data}
            result = CommandResult.success(action=cmd.action, data=data)
        except Exception as exc:
            from vdisplay.application.errors import error_from_exception

            result = CommandResult.failure(action=cmd.action, error=error_from_exception(exc))
        duration_ms = int((time.perf_counter() - started) * 1000)
        result.diagnostics = extract_diagnostics(result)
        record_execution(cmd, result, route="local", duration_ms=duration_ms)
        return _json_from_command_result(action, result)


def _json_from_command_result(action: str, result: CommandResult) -> JSONResponse:
    data = dict(result.data or {})
    if result.error is not None:
        data["error"] = result.error.to_dict()
    meta = dict(result.meta or {})
    if result.session_id and "session_id" not in meta:
        meta["session_id"] = result.session_id
    session_dir = meta.get("session_dir")
    if session_dir:
        meta["session_dir"] = session_dir
    envelope = from_runtime(action, {**data, "ok": result.ok}, meta=meta)
    status = 200 if result.ok else 400
    return JSONResponse(envelope, status_code=status)


# Backward-compatible alias used by control routes.
execute_control_route = execute_audit_route
