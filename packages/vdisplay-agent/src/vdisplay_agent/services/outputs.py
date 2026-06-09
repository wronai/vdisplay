"""Monitor/output discovery for the broker."""

from __future__ import annotations

import os
from typing import Any

from vdisplay.discovery import list_outputs, resolve_host_display


def list_outputs_payload(*, display: str | None = None, include_all: bool = True) -> dict[str, Any]:
    resolved = resolve_host_display(display)
    monitors = list_outputs(resolved, enrich_nl=False, apps_only=not include_all)
    return {
        "requested_display": display or os.environ.get("DISPLAY"),
        "resolved_display": resolved,
        "monitor_count": len(monitors),
        "monitors": monitors,
    }
