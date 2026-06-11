"""Application data models."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from ..errors import ApplicationError
from .verbs import CommandVerb

_CONTROL_ACTIONS = {
    "CONTROLS_LIST": "controls_list",
    "CONTROLS_FIND": "controls_find",
    "CONTROL_CLICK": "control_click",
    "CONTROL_FOCUS": "control_focus",
    "CONTROL_SET_VALUE": "control_set_value",
    "DIAGNOSE_CONTROL": "diagnose_control",
}


@dataclass
class ArtifactRef:
    kind: str
    path: str
    label: str | None = None
    role: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"kind": self.kind, "path": self.path}
        if self.label is not None:
            payload["label"] = self.label
        if self.role is not None:
            payload["role"] = self.role
        return payload


@dataclass
class CommandRequest:
    verb: CommandVerb
    line: str = ""
    request_source: str = "cli"
    session_id: str | None = None
    request_id: str | None = None
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
    terminal_session_id: str | None = None
    terminal_command: str | None = None
    terminal_rows: int = 24
    terminal_cols: int = 80
    terminal_title: str | None = None
    browser_session_id: str | None = None
    browser_url: str | None = None
    browser_headless: bool = True
    browser_title: str | None = None
    browser_engine: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def action(self) -> str:
        if self.verb == CommandVerb.OUTPUTS:
            return "outputs"
        if self.verb.value in _CONTROL_ACTIONS:
            return _CONTROL_ACTIONS[self.verb.value]
        return self.verb.value.lower()

    @classmethod
    def from_dsl(cls, cmd: dict[str, Any], *, line: str = "") -> CommandRequest:
        from .parsers import parse_dsl

        return parse_dsl(cmd, line=line)

    @classmethod
    def from_agent_body(
        cls,
        verb: CommandVerb,
        body: dict[str, Any],
        *,
        audit: Any,
    ) -> CommandRequest:
        from .parsers import parse_agent_body

        return parse_agent_body(verb, body, audit=audit)


@dataclass
class CommandResult:
    ok: bool
    action: str
    data: dict[str, Any] = field(default_factory=dict)
    error: ApplicationError | None = None
    meta: dict[str, Any] = field(default_factory=dict)
    command: str = ""
    artifacts: list[ArtifactRef] = field(default_factory=list)
    diagnostics: dict[str, Any] = field(default_factory=dict)
    session_id: str | None = None
    request_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "ok": self.ok,
            "action": self.action,
            "data": self.data,
            "meta": self.meta,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "diagnostics": self.diagnostics,
        }
        if self.command:
            payload["command"] = self.command
        if self.session_id:
            payload["session_id"] = self.session_id
        if self.request_id:
            payload["request_id"] = self.request_id
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
        artifacts: list[ArtifactRef] | None = None,
        diagnostics: dict[str, Any] | None = None,
    ) -> CommandResult:
        return cls(
            ok=True,
            action=action,
            data=data,
            command=command,
            meta=meta or {},
            artifacts=artifacts or [],
            diagnostics=diagnostics or {},
        )

    @classmethod
    def failure(
        cls,
        *,
        action: str,
        error: ApplicationError,
        data: dict[str, Any] | None = None,
        command: str = "",
        meta: dict[str, Any] | None = None,
        artifacts: list[ArtifactRef] | None = None,
        diagnostics: dict[str, Any] | None = None,
    ) -> CommandResult:
        return cls(
            ok=False,
            action=action,
            data=data or {},
            error=error,
            command=command,
            meta=meta or {},
            artifacts=artifacts or [],
            diagnostics=diagnostics or {},
        )