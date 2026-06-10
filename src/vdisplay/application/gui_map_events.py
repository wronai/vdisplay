"""Emit GuiMap* domain events into the active audit session."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .events import DomainEvent, gui_map_built, gui_map_drift_detected
from .projections.backend_scores import resolve_active_session_root


def _session_id(session_root: Path) -> str | None:
    session_json = session_root / "session.json"
    if not session_json.is_file():
        return session_root.name
    try:
        import json

        payload = json.loads(session_json.read_text(encoding="utf-8"))
        return str(payload.get("session_id") or session_root.name)
    except Exception:
        return session_root.name


def emit_gui_map_event(event: DomainEvent) -> None:
    from .event_store import append_event, event_store_enabled

    if not event_store_enabled():
        return
    session_root = resolve_active_session_root()
    if session_root is None:
        return
    if event.session_id is None:
        event = DomainEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            occurred_at_ms=event.occurred_at_ms,
            session_id=_session_id(session_root),
            request_id=event.request_id,
            aggregate=event.aggregate,
            body=event.body,
        )
    append_event(session_root, event)


def record_gui_map_built(
    *,
    map_path: str,
    element_count: int,
    region_count: int = 0,
    map_id: str | None = None,
    scope_ids: list[str] | None = None,
    request_id: str | None = None,
) -> None:
    session_root = resolve_active_session_root()
    emit_gui_map_event(
        gui_map_built(
            session_id=_session_id(session_root) if session_root else None,
            request_id=request_id,
            map_path=map_path,
            map_id=map_id,
            element_count=element_count,
            region_count=region_count,
            scope_ids=scope_ids,
        )
    )


def record_gui_map_drift(
    *,
    map_path: str,
    drift: dict[str, Any],
    scope_id: str | None = None,
    request_id: str | None = None,
) -> None:
    session_root = resolve_active_session_root()
    summary = drift.get("summary") if isinstance(drift.get("summary"), dict) else {}
    changed_targets = drift.get("key_targets") or drift.get("changed_targets")
    emit_gui_map_event(
        gui_map_drift_detected(
            session_id=_session_id(session_root) if session_root else None,
            request_id=request_id,
            map_path=map_path,
            scope_id=scope_id,
            drifted=bool(drift.get("drifted", True)),
            recommendation=str(drift.get("recommendation") or ""),
            actionable=bool(drift.get("actionable")),
            summary=summary,
            changed_targets=list(changed_targets) if isinstance(changed_targets, dict) else changed_targets,
        )
    )
