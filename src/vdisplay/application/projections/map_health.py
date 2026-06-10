"""GUI map drift and refresh health projection."""

from __future__ import annotations

from typing import Any

from ..events import DomainEvent


def _ensure_map_entry(health: dict[str, Any], map_path: str) -> dict[str, Any]:
    by_path = health.setdefault("by_map_path", {})
    entry = by_path.setdefault(
        map_path,
        {
            "map_path": map_path,
            "drift_count": 0,
            "layout_failures": 0,
            "refresh_required": False,
            "scopes": {},
        },
    )
    return entry


def _apply_drift_payload(
    entry: dict[str, Any],
    *,
    occurred_at_ms: int,
    drift: dict[str, Any],
    scope_id: str | None = None,
) -> None:
    entry["drift_count"] = int(entry.get("drift_count") or 0) + 1
    entry["last_drift_ms"] = occurred_at_ms
    recommendation = str(drift.get("recommendation") or "").lower()
    if recommendation == "refresh_required" or drift.get("actionable") is True:
        entry["refresh_required"] = True

    summary = drift.get("summary") if isinstance(drift.get("summary"), dict) else {}
    scope_key = scope_id or "default"
    scopes = entry.setdefault("scopes", {})
    scope_entry = scopes.setdefault(
        scope_key,
        {"missing": 0, "bounds": 0, "fingerprint": 0, "drift_events": 0},
    )
    scope_entry["drift_events"] = int(scope_entry.get("drift_events") or 0) + 1
    scope_entry["missing"] = max(int(scope_entry.get("missing") or 0), int(summary.get("missing") or 0))
    scope_entry["bounds"] = max(int(scope_entry.get("bounds") or 0), int(summary.get("bounds") or 0))
    scope_entry["fingerprint"] = max(
        int(scope_entry.get("fingerprint") or 0),
        int(summary.get("fingerprint") or 0),
    )
    scope_entry["last_drift_ms"] = occurred_at_ms
    if recommendation:
        scope_entry["recommendation"] = recommendation


def build_map_health(events: list[DomainEvent]) -> dict[str, Any]:
    health: dict[str, Any] = {"by_map_path": {}, "updated_at_ms": 0}

    for event in events:
        health["updated_at_ms"] = max(int(health["updated_at_ms"]), event.occurred_at_ms)

        if event.event_type == "GuiMapBuilt":
            map_path = str(event.body.get("path") or event.body.get("map_path") or "")
            if not map_path:
                continue
            entry = _ensure_map_entry(health, map_path)
            entry["map_id"] = event.body.get("map_id")
            entry["element_count"] = int(event.body.get("element_count") or 0)
            entry["region_count"] = int(event.body.get("region_count") or 0)
            entry["built_at_ms"] = event.occurred_at_ms
            if event.body.get("scope_ids"):
                entry["scope_ids"] = list(event.body["scope_ids"])
            continue

        if event.event_type == "GuiMapDriftDetected":
            map_path = str(event.body.get("path") or event.body.get("map_path") or "")
            if not map_path:
                continue
            entry = _ensure_map_entry(health, map_path)
            drift = {
                "recommendation": event.body.get("recommendation"),
                "actionable": event.body.get("actionable"),
                "summary": event.body.get("summary") or {},
                "drifted": event.body.get("drifted", True),
            }
            _apply_drift_payload(
                entry,
                occurred_at_ms=event.occurred_at_ms,
                drift=drift,
                scope_id=event.body.get("scope_id"),
            )
            if event.body.get("changed_targets"):
                entry["changed_targets"] = list(event.body["changed_targets"])
            continue

        if event.event_type not in {"StepRecorded", "CommandCompleted", "ControlVerificationFailed"}:
            continue

        diagnostics = event.body.get("diagnostics") if isinstance(event.body.get("diagnostics"), dict) else {}
        control = diagnostics.get("control") if isinstance(diagnostics.get("control"), dict) else {}
        verify = control.get("verify") if isinstance(control.get("verify"), dict) else diagnostics.get("verify")
        if not isinstance(verify, dict):
            verify = {}

        map_block = control.get("map") if isinstance(control.get("map"), dict) else {}
        map_path = str(map_block.get("path") or event.body.get("map_path") or "")
        drift = verify.get("map_drift") or verify.get("gui_map_drift")
        if map_path and isinstance(drift, dict) and drift.get("drifted"):
            entry = _ensure_map_entry(health, map_path)
            _apply_drift_payload(
                entry,
                occurred_at_ms=event.occurred_at_ms,
                drift=drift,
                scope_id=map_block.get("scope") or map_block.get("scope_id"),
            )

        if event.event_type == "ControlVerificationFailed":
            phases = verify.get("phases") if isinstance(verify.get("phases"), list) else []
            for phase in phases:
                if not isinstance(phase, dict) or phase.get("phase") != "layout":
                    continue
                payload = phase.get("payload") if isinstance(phase.get("payload"), dict) else {}
                if payload.get("ok") is not False:
                    continue
                if not map_path:
                    map_path = str(map_block.get("path") or "unknown")
                entry = _ensure_map_entry(health, map_path)
                entry["layout_failures"] = int(entry.get("layout_failures") or 0) + 1
                entry["refresh_required"] = True
                entry["last_layout_failure_ms"] = event.occurred_at_ms

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
