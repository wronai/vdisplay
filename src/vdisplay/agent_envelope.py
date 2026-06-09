"""Flatten vdisplay-agent JSON envelopes for SDK clients."""

from __future__ import annotations

from typing import Any


def flatten_agent_envelope(payload: dict[str, Any]) -> dict[str, Any]:
    """Merge envelope.data to top level for backward-compatible clients."""
    if "data" in payload and "action" in payload:
        flat = dict(payload.get("data") or {})
        if "ok" in payload:
            flat["ok"] = payload["ok"]
        if payload.get("error"):
            flat["error"] = payload["error"]
        return flat
    return payload
