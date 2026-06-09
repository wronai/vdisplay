from __future__ import annotations

from typing import Any

from dsl2vdisplay.grammar import parse_line, split_command, to_text
from dsl2vdisplay.result import DslResult
from dsl2vdisplay.schema_registry import validate_command_dict

QUERY_VERBS = frozenset({"HEALTH", "INFO", "OUTPUTS", "WINDOWS", "CAPABILITIES", "VALIDATE"})
COMMAND_VERBS = frozenset({"SCREENSHOT", "VIRTUAL_START", "VIRTUAL_STOP", "LAUNCH", "MIRROR", "ADOPT", "RELEASE"})


def _dispatch_query(cmd: dict[str, Any], *, line: str) -> DslResult:
    from dsl2vdisplay.handlers import query as qh

    verb = str(cmd.get("verb", "")).upper()
    handlers = {
        "HEALTH": qh.handle_health,
        "INFO": qh.handle_info,
        "OUTPUTS": qh.handle_outputs,
        "WINDOWS": qh.handle_windows,
        "CAPABILITIES": qh.handle_capabilities,
        "VALIDATE": qh.handle_validate,
    }
    handler = handlers.get(verb)
    if handler is None:
        return DslResult(ok=False, command=line, action=verb.lower(), error=f"unknown query verb: {verb}")
    return handler(cmd, line=line)


def _dispatch_cmd(cmd: dict[str, Any], *, line: str) -> DslResult:
    from dsl2vdisplay.handlers import command as ch

    verb = str(cmd.get("verb", "")).upper()
    errors = validate_command_dict(cmd)
    if errors:
        return DslResult(ok=False, command=line, action=verb.lower(), error="; ".join(errors))

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
    if verb in QUERY_VERBS:
        return _dispatch_query(cmd, line=line)
    if verb in COMMAND_VERBS:
        return _dispatch_cmd(cmd, line=line)
    return DslResult(ok=False, command=line, action=verb.lower(), error=f"unknown verb: {verb}")


def execute_dsl_line(line: str) -> DslResult:
    return dispatch(line)
