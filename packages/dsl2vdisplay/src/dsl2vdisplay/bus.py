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
    # VIRTUAL_STOP / LAUNCH have no DSL handler (never implemented); validate the
    # envelope then report them as unsupported over this path.
    verb = str(cmd.get("verb", "")).upper()
    errors = validate_command_dict(cmd)
    if errors:
        return DslResult(ok=False, command=line, action=verb.lower(), error="; ".join(errors))
    return DslResult(ok=False, command=line, action=verb.lower(), error=f"unknown command verb: {verb}")


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

    # vdisplay is a hard dependency of dsl2vdisplay, so the application layer is
    # always importable — route straight through the executor (the single
    # contract). No local re-implementation fallback.
    from vdisplay.application.commands import CommandRequest
    from vdisplay.application.executor import execute

    request = CommandRequest.from_dsl(cmd, line=line)
    return execute(request).to_dsl_result()


def execute_dsl_line(line: str) -> DslResult:
    return dispatch(line)
