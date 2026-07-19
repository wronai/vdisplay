"""Monitor discovery adapter for typed observation providers."""

from __future__ import annotations

from ...discovery import list_monitors as discover_monitors
from .observation import MonitorSpec


def monitor_specs_from_discovery() -> list[MonitorSpec]:
    try:
        rows = discover_monitors()
    except Exception:  # noqa: BLE001 - discovery is advisory for capture.
        return []
    specs: list[MonitorSpec] = []
    for fallback_index, row in enumerate(rows):
        raw_index = row.get("monitor_index")
        specs.append(
            MonitorSpec(
                id=fallback_index if raw_index is None else int(raw_index),
                output=str(row.get("name") or f"monitor-{fallback_index}"),
                width=int(row.get("width") or 0),
                height=int(row.get("height") or 0),
                left=int(row.get("x") or 0),
                top=int(row.get("y") or 0),
                is_primary=bool(row.get("primary")),
            )
        )
    return specs


__all__ = ["monitor_specs_from_discovery"]
