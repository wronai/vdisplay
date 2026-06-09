"""Shared command model for CLI, DSL, REST, and agent client."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .errors import ApplicationError


class CommandVerb(StrEnum):
    HEALTH = "HEALTH"
    INFO = "INFO"
    OUTPUTS = "OUTPUTS"
    MONITORS = "MONITORS"
    WINDOWS = "WINDOWS"
    ALL = "ALL"
    CAPABILITIES = "CAPABILITIES"
    VALIDATE = "VALIDATE"
    SCREENSHOT = "SCREENSHOT"
    VIRTUAL_START = "VIRTUAL_START"
    VIRTUAL_STOP = "VIRTUAL_STOP"
    LAUNCH = "LAUNCH"
    MIRROR = "MIRROR"
    ADOPT = "ADOPT"
    RELEASE = "RELEASE"
    CONTROLS_LIST = "CONTROLS_LIST"
    CONTROLS_FIND = "CONTROLS_FIND"
    CONTROL_CLICK = "CONTROL_CLICK"
    CONTROL_FOCUS = "CONTROL_FOCUS"
    CONTROL_SET_VALUE = "CONTROL_SET_VALUE"
    DIAGNOSE_CONTROL = "DIAGNOSE_CONTROL"


QUERY_VERBS = frozenset(
    {
        CommandVerb.HEALTH,
        CommandVerb.INFO,
        CommandVerb.OUTPUTS,
        CommandVerb.MONITORS,
        CommandVerb.WINDOWS,
        CommandVerb.ALL,
        CommandVerb.CAPABILITIES,
        CommandVerb.VALIDATE,
        CommandVerb.CONTROLS_LIST,
        CommandVerb.CONTROLS_FIND,
        CommandVerb.DIAGNOSE_CONTROL,
    }
)

COMMAND_VERBS = frozenset(
    {
        CommandVerb.SCREENSHOT,
        CommandVerb.VIRTUAL_START,
        CommandVerb.VIRTUAL_STOP,
        CommandVerb.LAUNCH,
        CommandVerb.MIRROR,
        CommandVerb.ADOPT,
        CommandVerb.RELEASE,
        CommandVerb.CONTROL_CLICK,
        CommandVerb.CONTROL_FOCUS,
        CommandVerb.CONTROL_SET_VALUE,
    }
)

_CONTROL_ACTIONS = {
    CommandVerb.CONTROLS_LIST: "controls_list",
    CommandVerb.CONTROLS_FIND: "controls_find",
    CommandVerb.CONTROL_CLICK: "control_click",
    CommandVerb.CONTROL_FOCUS: "control_focus",
    CommandVerb.CONTROL_SET_VALUE: "control_set_value",
    CommandVerb.DIAGNOSE_CONTROL: "diagnose_control",
}


@dataclass
class CommandRequest:
    verb: CommandVerb
    line: str = ""
    display: str | None = None
    apps_only: bool = False
    include_all: bool = True
    match_class: str | None = None
    match_pid: int | None = None
    match_app: str | None = None
    match_title: str | None = None
    window_id: str | None = None
    min_width: int = 0
    min_height: int = 0
    output: str | None = None
    width: int = 1920
    height: int = 1080
    source: str | None = None
    target: str | None = None
    mode: str = "host"
    all_monitors: bool = False
    out_dir: str | None = None
    vd_display: str = ":99"
    backend: str = "xvfb"
    monitor: int | None = None
    local_only: bool = False
    control_selector: str | None = None
    control_provider_ref: str | None = None
    control_name: str | None = None
    control_role: str | None = None
    control_app: str | None = None
    control_window_id: str | None = None
    control_window_title: str | None = None
    control_value: str | None = None
    control_verify: bool = False
    control_screenshot_verify: bool = False
    control_verify_label: str | None = None
    control_verify_selector: str | None = None
    control_backend: str = "auto"
    control_index: int = 0
    control_max_depth: int = 8
    control_format: str = "flat"
    control_environment: str | None = None
    control_text: str | None = None
    control_text_contains: str | None = None
    control_terminal_line: int | None = None
    control_terminal_col: int | None = None
    control_session_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def action(self) -> str:
        if self.verb == CommandVerb.OUTPUTS:
            return "outputs"
        if self.verb in _CONTROL_ACTIONS:
            return _CONTROL_ACTIONS[self.verb]
        return self.verb.value.lower()

    @classmethod
    def from_dsl(cls, cmd: dict[str, Any], *, line: str = "") -> CommandRequest:
        verb_raw = str(cmd.get("verb", "HEALTH")).upper()
        try:
            verb = CommandVerb(verb_raw)
        except ValueError:
            verb = CommandVerb.HEALTH
        apps_only = bool(cmd.get("apps_only", False))
        return cls(
            verb=verb,
            line=line,
            display=cmd.get("display"),
            apps_only=apps_only,
            include_all=not apps_only,
            match_class=cmd.get("class"),
            match_pid=cmd.get("pid"),
            match_app=cmd.get("app"),
            match_title=cmd.get("title"),
            window_id=cmd.get("window_id"),
            output=cmd.get("out"),
            width=int(cmd.get("width", 1920)),
            height=int(cmd.get("height", 1080)),
            source=cmd.get("source"),
            target=cmd.get("target"),
            vd_display=str(cmd.get("display", ":99")),
            backend=str(cmd.get("backend", "xvfb")),
            control_selector=cmd.get("selector"),
            control_provider_ref=cmd.get("provider_ref") or cmd.get("id"),
            control_name=cmd.get("name"),
            control_role=cmd.get("role"),
            control_app=cmd.get("app"),
            control_window_id=cmd.get("window_id"),
            control_window_title=cmd.get("window_title"),
            control_value=cmd.get("value"),
            control_verify=bool(cmd.get("verify", False)),
            control_screenshot_verify=bool(cmd.get("screenshot_verify", False)),
            control_verify_label=cmd.get("verify_label"),
            control_verify_selector=cmd.get("verify_selector"),
            control_backend=str(cmd.get("control_backend") or cmd.get("backend") or "auto"),
            control_index=int(cmd.get("index") or 0),
            control_max_depth=int(cmd.get("max_depth") or 8),
            control_format=str(cmd.get("format") or "flat"),
            control_environment=cmd.get("environment"),
            control_text=cmd.get("text"),
            control_text_contains=cmd.get("text_contains"),
            control_terminal_line=int(cmd["terminal_line"]) if cmd.get("terminal_line") is not None else None,
            control_terminal_col=int(cmd["terminal_col"]) if cmd.get("terminal_col") is not None else None,
            control_session_id=cmd.get("session_id"),
            extra={k: v for k, v in cmd.items() if k not in {"verb"}},
        )


@dataclass
class CommandResult:
    ok: bool
    action: str
    data: dict[str, Any] = field(default_factory=dict)
    error: ApplicationError | None = None
    meta: dict[str, Any] = field(default_factory=dict)
    command: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "ok": self.ok,
            "action": self.action,
            "data": self.data,
            "meta": self.meta,
        }
        if self.command:
            payload["command"] = self.command
        if self.error is not None:
            payload["error"] = self.error.to_dict()
        return payload

    def to_dsl_result(self) -> Any:
        from dsl2vdisplay.result import DslResult

        return DslResult(
            ok=self.ok,
            command=self.command,
            action=self.action,
            output=json.dumps(self.data, indent=2, ensure_ascii=False) if self.ok else "",
            data=self.data,
            error=None if self.ok else (self.error.message if self.error else "unknown error"),
        )

    @classmethod
    def success(
        cls,
        *,
        action: str,
        data: dict[str, Any],
        command: str = "",
        meta: dict[str, Any] | None = None,
    ) -> CommandResult:
        return cls(ok=True, action=action, data=data, command=command, meta=meta or {})

    @classmethod
    def failure(
        cls,
        *,
        action: str,
        error: ApplicationError,
        data: dict[str, Any] | None = None,
        command: str = "",
        meta: dict[str, Any] | None = None,
    ) -> CommandResult:
        return cls(
            ok=False,
            action=action,
            data=data or {},
            error=error,
            command=command,
            meta=meta or {},
        )
