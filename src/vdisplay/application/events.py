"""Domain events for audit session event store."""

from __future__ import annotations

import socket
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from .commands import CommandRequest, CommandResult

_CONTROL_VERBS = {
    "CONTROLS_FIND",
    "CONTROLS_LIST",
    "CONTROL_CLICK",
    "CONTROL_FOCUS",
    "CONTROL_SET_VALUE",
    "DIAGNOSE_CONTROL",
}


@dataclass
class DomainEvent:
    event_id: str
    event_type: str
    occurred_at_ms: int
    session_id: str | None = None
    request_id: str | None = None
    aggregate: str | None = None
    body: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DomainEvent:
        return cls(
            event_id=str(payload.get("event_id") or uuid.uuid4()),
            event_type=str(payload.get("event_type") or "Unknown"),
            occurred_at_ms=int(payload.get("occurred_at_ms") or _now_ms()),
            session_id=payload.get("session_id"),
            request_id=payload.get("request_id"),
            aggregate=payload.get("aggregate"),
            body=dict(payload.get("body") or {}),
        )


def _now_ms() -> int:
    return int(time.time() * 1000)


def _event_id() -> str:
    return uuid.uuid4().hex


def session_started(*, session_id: str, source: str, route: str, env: dict[str, str]) -> DomainEvent:
    return DomainEvent(
        event_id=_event_id(),
        event_type="SessionStarted",
        occurred_at_ms=_now_ms(),
        session_id=session_id,
        aggregate="audit_session",
        body={
            "source": source,
            "route_default": route,
            "host": socket.gethostname(),
            "env": env,
        },
    )


def command_received(cmd: CommandRequest, *, route: str) -> DomainEvent:
    return DomainEvent(
        event_id=_event_id(),
        event_type="CommandReceived",
        occurred_at_ms=_now_ms(),
        session_id=cmd.session_id,
        request_id=cmd.request_id,
        aggregate="command",
        body={
            "verb": str(cmd.verb.value),
            "action": cmd.action,
            "source": cmd.request_source,
            "route": route,
            "command_line": cmd.line,
        },
    )


def command_completed(
    cmd: CommandRequest,
    result: CommandResult,
    *,
    route: str,
    duration_ms: int,
) -> DomainEvent:
    return DomainEvent(
        event_id=_event_id(),
        event_type="CommandCompleted",
        occurred_at_ms=_now_ms(),
        session_id=cmd.session_id or result.session_id,
        request_id=cmd.request_id or result.request_id,
        aggregate="command",
        body={
            "verb": str(cmd.verb.value),
            "action": result.action,
            "ok": result.ok,
            "route": route,
            "duration_ms": duration_ms,
            "error": result.error.to_dict() if result.error else None,
            "diagnostics": dict(result.diagnostics or {}),
        },
    )


def step_recorded(
    *,
    session_id: str,
    request_id: str,
    step_id: str,
    route: str,
    verb: str,
    ok: bool,
    duration_ms: int,
    request_path: str,
    result_path: str,
    diagnostics: dict[str, Any],
) -> DomainEvent:
    return DomainEvent(
        event_id=_event_id(),
        event_type="StepRecorded",
        occurred_at_ms=_now_ms(),
        session_id=session_id,
        request_id=request_id,
        aggregate="command",
        body={
            "step_id": step_id,
            "route": route,
            "verb": verb,
            "ok": ok,
            "duration_ms": duration_ms,
            "request_path": request_path,
            "result_path": result_path,
            "diagnostics": diagnostics,
        },
    )


def control_events_from_diagnostics(
    *,
    session_id: str | None,
    request_id: str | None,
    verb: str,
    diagnostics: dict[str, Any],
    ok: bool,
) -> list[DomainEvent]:
    if verb not in _CONTROL_VERBS:
        return []

    events: list[DomainEvent] = []
    control = diagnostics.get("control") if isinstance(diagnostics.get("control"), dict) else {}
    routing = control.get("routing") if isinstance(control.get("routing"), dict) else diagnostics.get("routing")
    verify = control.get("verify") if isinstance(control.get("verify"), dict) else diagnostics.get("verify")

    if isinstance(routing, dict) and routing.get("selected_provider"):
        events.append(
            DomainEvent(
                event_id=_event_id(),
                event_type="ControlActionPlanned",
                occurred_at_ms=_now_ms(),
                session_id=session_id,
                request_id=request_id,
                aggregate="control_action",
                body={
                    "verb": verb,
                    "action_id": control.get("action_id"),
                    "attempt": control.get("attempt"),
                    "routing": routing,
                    "map": control.get("map"),
                    "target": control.get("target"),
                },
            )
        )
    elif control.get("action") or control.get("target"):
        events.append(
            DomainEvent(
                event_id=_event_id(),
                event_type="ControlActionPlanned",
                occurred_at_ms=_now_ms(),
                session_id=session_id,
                request_id=request_id,
                aggregate="control_action",
                body={
                    "verb": verb,
                    "action": control.get("action"),
                    "action_id": control.get("action_id"),
                    "target": control.get("target"),
                    "map": control.get("map"),
                },
            )
        )

    actuation = control.get("actuation")
    if isinstance(actuation, dict) and actuation:
        events.append(
            DomainEvent(
                event_id=_event_id(),
                event_type="ControlActionExecuted",
                occurred_at_ms=_now_ms(),
                session_id=session_id,
                request_id=request_id,
                aggregate="control_action",
                body={
                    "verb": verb,
                    "action_id": control.get("action_id"),
                    "actuation": actuation,
                },
            )
        )
    elif control.get("action") and ok and verb in {"CONTROL_CLICK", "CONTROL_FOCUS", "CONTROL_SET_VALUE"}:
        events.append(
            DomainEvent(
                event_id=_event_id(),
                event_type="ControlActionExecuted",
                occurred_at_ms=_now_ms(),
                session_id=session_id,
                request_id=request_id,
                aggregate="control_action",
                body={
                    "verb": verb,
                    "action": control.get("action"),
                    "action_id": control.get("action_id"),
                    "ok": ok,
                },
            )
        )

    if isinstance(verify, dict) and verify:
        verified = verify.get("verified")
        event_type = "ControlVerificationPassed" if verified else "ControlVerificationFailed"
        if ok and verified is None:
            event_type = "ControlVerificationPassed" if ok else "ControlVerificationFailed"
        events.append(
            DomainEvent(
                event_id=_event_id(),
                event_type=event_type,
                occurred_at_ms=_now_ms(),
                session_id=session_id,
                request_id=request_id,
                aggregate="control_action",
                body={"verb": verb, "verify": verify},
            )
        )

    retry = control.get("retry") if isinstance(control.get("retry"), dict) else {}
    if retry.get("strategy"):
        events.append(
            DomainEvent(
                event_id=_event_id(),
                event_type="ControlRetryScheduled",
                occurred_at_ms=_now_ms(),
                session_id=session_id,
                request_id=request_id,
                aggregate="control_action",
                body={
                    "verb": verb,
                    "attempt": control.get("attempt"),
                    "strategy": retry.get("strategy"),
                    "next_backend": retry.get("next_backend"),
                    "reason": retry.get("reason"),
                },
            )
        )

    recovery = control.get("recovery_failed") if isinstance(control.get("recovery_failed"), dict) else {}
    if recovery:
        events.append(
            DomainEvent(
                event_id=_event_id(),
                event_type="ControlRecoveryFailed",
                occurred_at_ms=_now_ms(),
                session_id=session_id,
                request_id=request_id,
                aggregate="control_action",
                body={"verb": verb, **recovery},
            )
        )

    return events


def gui_map_built(
    *,
    session_id: str | None,
    request_id: str | None,
    map_path: str,
    element_count: int,
    region_count: int = 0,
    map_id: str | None = None,
    scope_ids: list[str] | None = None,
) -> DomainEvent:
    return DomainEvent(
        event_id=_event_id(),
        event_type="GuiMapBuilt",
        occurred_at_ms=_now_ms(),
        session_id=session_id,
        request_id=request_id,
        aggregate="gui_map",
        body={
            "path": map_path,
            "map_path": map_path,
            "map_id": map_id,
            "element_count": element_count,
            "region_count": region_count,
            "scope_ids": scope_ids or [],
        },
    )


def gui_map_drift_detected(
    *,
    session_id: str | None,
    request_id: str | None,
    map_path: str,
    scope_id: str | None = None,
    drifted: bool = True,
    recommendation: str = "",
    actionable: bool = False,
    summary: dict[str, Any] | None = None,
    changed_targets: list[Any] | None = None,
) -> DomainEvent:
    return DomainEvent(
        event_id=_event_id(),
        event_type="GuiMapDriftDetected",
        occurred_at_ms=_now_ms(),
        session_id=session_id,
        request_id=request_id,
        aggregate="gui_map",
        body={
            "path": map_path,
            "map_path": map_path,
            "scope_id": scope_id,
            "drifted": drifted,
            "recommendation": recommendation,
            "actionable": actionable,
            "summary": dict(summary or {}),
            "changed_targets": changed_targets or [],
        },
    )


def map_events_from_diagnostics(
    *,
    session_id: str,
    request_id: str,
    diagnostics: dict[str, Any],
) -> list[DomainEvent]:
    events: list[DomainEvent] = []
    control = diagnostics.get("control") if isinstance(diagnostics.get("control"), dict) else {}
    verify = control.get("verify") if isinstance(control.get("verify"), dict) else diagnostics.get("verify")
    if not isinstance(verify, dict):
        return events
    map_block = control.get("map") if isinstance(control.get("map"), dict) else {}
    map_path = str(map_block.get("path") or "")
    if not map_path:
        return events
    drift = verify.get("map_drift") or verify.get("gui_map_drift")
    if isinstance(drift, dict) and drift.get("drifted"):
        summary = drift.get("summary") if isinstance(drift.get("summary"), dict) else {}
        events.append(
            gui_map_drift_detected(
                session_id=session_id,
                request_id=request_id,
                map_path=map_path,
                scope_id=map_block.get("scope") or map_block.get("scope_id"),
                drifted=bool(drift.get("drifted", True)),
                recommendation=str(drift.get("recommendation") or ""),
                actionable=bool(drift.get("actionable")),
                summary=summary,
                changed_targets=(
                    list(drift.get("key_targets").keys())
                    if isinstance(drift.get("key_targets"), dict)
                    else drift.get("changed_targets")
                ),
            )
        )
    return events
