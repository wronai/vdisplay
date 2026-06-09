"""Resolve vdisplay-agent connection (install-once broker for all client apps)."""

from __future__ import annotations

import os


def resolve_agent_url(explicit: str | None = None) -> str | None:
    """Return agent base URL when clients should use IPC instead of in-process capture."""
    url = (explicit or os.environ.get("VDISPLAY_AGENT_URL") or "").strip()
    return url.rstrip("/") if url else None


def resolve_agent_token() -> str | None:
    token = (os.environ.get("VDISPLAY_AGENT_TOKEN") or "").strip()
    return token or None


def use_agent(explicit: str | None = None) -> bool:
    if os.environ.get("VDISPLAY_AGENT_BROKER", "").strip().lower() in {"1", "true", "yes"}:
        return False
    return resolve_agent_url(explicit) is not None
