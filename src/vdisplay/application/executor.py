"""Execute CommandRequest via agent or local application services."""

from __future__ import annotations

from typing import Any

from .commands import CommandRequest, CommandResult, CommandVerb
from .errors import error_from_exception
from .handlers import execute_agent, execute_local
from .runtime import ExecutionPolicy, Route, get_execution_policy
from ..exceptions import VDisplayError


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
    pol = policy or get_execution_policy()
    route = force_route or pol.route(cmd)
    meta = pol.meta_for(route)
    try:
        data = execute_agent(cmd) if route == "agent" else execute_local(cmd)
        data = _maybe_enrich_screenshot(cmd, data)
        return CommandResult.success(action=cmd.action, data=data, command=cmd.line, meta=meta)
    except VDisplayError as exc:
        return CommandResult.failure(
            action=cmd.action,
            error=error_from_exception(exc),
            command=cmd.line,
            meta=meta,
        )
    except Exception as exc:
        return CommandResult.failure(
            action=cmd.action,
            error=error_from_exception(exc),
            command=cmd.line,
            meta=meta,
        )
