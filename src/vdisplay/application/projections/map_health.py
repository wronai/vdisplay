"""GUI map drift and refresh health projection."""

from __future__ import annotations

from typing import Any

from ..events import DomainEvent
from .map_health_handlers import apply_gui_map_built, apply_gui_map_drift, apply_step_verify_drift


def build_map_health(events: list[DomainEvent]) -> dict[str, Any]:
    health: dict[str, Any] = {"by_map_path": {}, "updated_at_ms": 0}

    for event in events:
        health["updated_at_ms"] = max(int(health["updated_at_ms"]), event.occurred_at_ms)

        if event.event_type == "GuiMapBuilt":
            apply_gui_map_built(health, event)
            continue
        if event.event_type == "GuiMapDriftDetected":
            apply_gui_map_drift(health, event)
            continue
        if event.event_type not in {"StepRecorded", "CommandCompleted", "ControlVerificationFailed"}:
            continue
        apply_step_verify_drift(health, event)

    return health


def load_map_health(session_root) -> dict[str, Any]:
    from pathlib import Path

    from ..event_store import EventStore

    root = Path(session_root)
    path = root / "projections" / "map_health.json"
    if path.is_file():
        import json

        return json.loads(path.read_text(encoding="utf-8"))
    return build_map_health(EventStore(root).read_all())
