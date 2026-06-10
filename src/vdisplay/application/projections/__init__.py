"""Read models rebuilt from index.jsonl."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..event_store import EventStore, read_events
from ..events import DomainEvent
from .backend_scores import build_backend_scores, load_backend_scores, load_merged_backend_scores, merge_backend_scores
from .map_health import build_map_health, load_map_health


def refresh_projections(session_root: Path | None) -> None:
    if session_root is None or not session_root.is_dir():
        return
    events = read_events(session_root)
    if not events:
        return
    out_dir = session_root / "projections"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "backend_scores.json").write_text(
        json.dumps(build_backend_scores(events), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (out_dir / "control_state.json").write_text(
        json.dumps(build_control_state(events), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (out_dir / "map_health.json").write_text(
        json.dumps(build_map_health(events), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def build_control_state(events: list[DomainEvent]) -> dict[str, Any]:
    state: dict[str, Any] = {"latest_by_request_id": {}, "updated_at_ms": 0}
    for event in events:
        if event.event_type not in {
            "ControlActionPlanned",
            "ControlActionExecuted",
            "ControlVerificationPassed",
            "ControlVerificationFailed",
            "ControlRetryScheduled",
            "ControlRecoveryFailed",
            "StepRecorded",
        }:
            continue
        request_id = event.request_id
        if not request_id:
            continue
        entry = state["latest_by_request_id"].setdefault(
            request_id,
            {"request_id": request_id, "events": []},
        )
        entry["events"].append(
            {
                "event_type": event.event_type,
                "occurred_at_ms": event.occurred_at_ms,
                "body": event.body,
            }
        )
        entry["last_event_type"] = event.event_type
        entry["last_occurred_at_ms"] = event.occurred_at_ms
        if event.event_type == "StepRecorded":
            entry["step_id"] = event.body.get("step_id")
            entry["ok"] = event.body.get("ok")
            entry["diagnostics"] = event.body.get("diagnostics")
        state["updated_at_ms"] = max(int(state["updated_at_ms"]), event.occurred_at_ms)
    return state


__all__ = [
    "build_backend_scores",
    "build_control_state",
    "build_map_health",
    "load_backend_scores",
    "load_map_health",
    "load_merged_backend_scores",
    "merge_backend_scores",
    "refresh_projections",
]
