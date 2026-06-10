"""Control action lifecycle state (PR-D)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace
from enum import StrEnum
from typing import Any


class ControlActionPhase(StrEnum):
    PLANNED = "planned"
    OBSERVED_PRE = "observed_pre"
    EXECUTED = "executed"
    OBSERVED_POST = "observed_post"
    VERIFYING = "verifying"
    VERIFIED = "verified"
    FAILED = "failed"
    RETRY_SCHEDULED = "retry_scheduled"
    RECOVERED = "recovered"
    RECOVERY_FAILED = "recovery_failed"


@dataclass
class ControlActionState:
    action_id: str
    action: str
    phase: ControlActionPhase = ControlActionPhase.PLANNED
    attempt: int = 1
    routing: dict[str, Any] = field(default_factory=dict)
    verify: dict[str, Any] = field(default_factory=dict)
    retry: dict[str, Any] = field(default_factory=dict)
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    event_ids: list[str] = field(default_factory=list)

    @classmethod
    def new(cls, action: str, *, action_id: str | None = None) -> ControlActionState:
        return cls(action_id=action_id or uuid.uuid4().hex[:16], action=action)

    def advance(self, phase: ControlActionPhase, **updates: Any) -> ControlActionState:
        payload = replace(self, phase=phase)
        for key, value in updates.items():
            if hasattr(payload, key):
                payload = replace(payload, **{key: value})
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action": self.action,
            "phase": self.phase.value,
            "attempt": self.attempt,
            "routing": dict(self.routing),
            "verify": dict(self.verify),
            "retry": dict(self.retry),
            "artifacts": list(self.artifacts),
            "event_ids": list(self.event_ids),
        }


def phase_from_payload(payload: dict[str, Any]) -> ControlActionPhase:
    if payload.get("ok"):
        return ControlActionPhase.VERIFIED
    verify = (payload.get("diagnostics") or {}).get("control", {}).get("verify", {})
    if verify.get("verified") is False or payload.get("verified") is False:
        return ControlActionPhase.FAILED
    if payload.get("ok") is False:
        return ControlActionPhase.FAILED
    return ControlActionPhase.EXECUTED
