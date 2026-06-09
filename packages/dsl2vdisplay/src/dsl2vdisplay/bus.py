from __future__ import annotations

from typing import Any

from dsl2vdisplay.grammar import parse_line, split_command, to_text
from dsl2vdisplay.result import DslResult
from dsl2vdisplay.schema_registry import validate_command_dict

QUERY_VERBS = frozenset({
    "HEALTH",
    "INFO",
    "OUTPUTS",
    "MONITORS",
    "WINDOWS",
    "ALL",
    "CAPABILITIES",
    "VALIDATE",
    "CONTROLS_LIST",
    "CONTROLS_FIND",
    "DIAGNOSE_CONTROL",
})
COMMAND_VERBS = frozenset({
    "SCREENSHOT",
    "VIRTUAL_START",
    "VIRTUAL_STOP",
    "LAUNCH",
    "MIRROR",
    "ADOPT",
    "RELEASE",
    "CONTROL_CLICK",
    "CONTROL_FOCUS",
    "CONTROL_SET_VALUE",
    "TERMINAL_OPEN",
    "BROWSER_OPEN",
})
LEGACY_COMMAND_VERBS = frozenset({"VIRTUAL_STOP", "LAUNCH"})


def _dispatch_legacy(cmd: dict[str, Any], *, line: str) -> DslResult:
    from dsl2vdisplay.handlers import command as ch

    verb = str(cmd.get("verb", "")).upper()
    errors = validate_command_dict(cmd)
    if errors:
        return DslResult(ok=False, command=line, action=verb.lower(), error="; ".join(errors))

    handlers = {
        "VIRTUAL_STOP": getattr(ch, "handle_virtual_stop", None),
        "LAUNCH": getattr(ch, "handle_launch", None),
    }
    handler = handlers.get(verb)
    if handler is None:
        return DslResult(ok=False, command=line, action=verb.lower(), error=f"unknown command verb: {verb}")
    return handler(cmd, line=line)


def dispatch(envelope: str | dict[str, Any] | bytes) -> DslResult:
    if isinstance(envelope, bytes):
        line = envelope.decode("utf-8").strip()
        cmd = parse_line(line) or {"verb": "NOOP"}
    elif isinstance(envelope, dict):
        line = to_text(envelope)
        cmd = envelope
    else:
        line = str(envelope).strip()
        tokens = split_command(line)
        if not tokens:
            return DslResult(ok=True, command=line, action="noop")
        cmd = parse_line(line) or {"verb": tokens[0].upper()}

    verb = str(cmd.get("verb", "")).upper()
    if verb == "NOOP":
        return DslResult(ok=True, command=line, action="noop")

    if verb in LEGACY_COMMAND_VERBS:
        return _dispatch_legacy(cmd, line=line)

    if verb in COMMAND_VERBS or verb in {
        "CONTROLS_LIST",
        "CONTROLS_FIND",
        "DIAGNOSE_CONTROL",
    }:
        errors = validate_command_dict(cmd)
        if errors:
            return DslResult(ok=False, command=line, action=verb.lower(), error="; ".join(errors))

    if verb not in QUERY_VERBS and verb not in COMMAND_VERBS:
        return DslResult(ok=False, command=line, action=verb.lower(), error=f"unknown verb: {verb}")

    try:
        from vdisplay.application.commands import CommandRequest
        from vdisplay.application.executor import execute

        request = CommandRequest.from_dsl(cmd, line=line)
        return execute(request).to_dsl_result()
    except ImportError:
        return _dispatch_fallback(cmd, line=line)


def _dispatch_fallback(cmd: dict[str, Any], *, line: str) -> DslResult:
    """Fallback when vdisplay application layer is unavailable."""
    verb = str(cmd.get("verb", "")).upper()
    if verb in QUERY_VERBS:
        from dsl2vdisplay.handlers import query as qh

        handlers = {
            "HEALTH": qh.handle_health,
            "INFO": qh.handle_info,
            "OUTPUTS": qh.handle_outputs,
            "MONITORS": qh.handle_monitors,
            "WINDOWS": qh.handle_windows,
            "ALL": qh.handle_all,
            "CAPABILITIES": qh.handle_capabilities,
            "VALIDATE": qh.handle_validate,
        }
        handler = handlers.get(verb)
        if handler is None:
            return DslResult(ok=False, command=line, action=verb.lower(), error=f"unknown query verb: {verb}")
        return handler(cmd, line=line)

    from dsl2vdisplay.handlers import command as ch

    handlers = {
        "SCREENSHOT": ch.handle_screenshot,
        "VIRTUAL_START": ch.handle_virtual_start,
        "MIRROR": ch.handle_mirror,
        "ADOPT": ch.handle_adopt,
        "RELEASE": ch.handle_release,
    }
    handler = handlers.get(verb)
    if handler is None:
        return DslResult(ok=False, command=line, action=verb.lower(), error=f"unknown command verb: {verb}")
    return handler(cmd, line=line)


def execute_dsl_line(line: str) -> DslResult:
    return dispatch(line)
