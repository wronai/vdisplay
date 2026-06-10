"""Resolve vdisplay-agent connection (install-once broker for all client apps)."""

from __future__ import annotations

import os
import urllib.error
import urllib.request

_PROBE_SENTINEL = object()
_probe_cache: str | None | object = _PROBE_SENTINEL


def agent_auto_enabled() -> bool:
    return os.environ.get("VDISPLAY_AGENT_AUTO", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def reset_agent_probe_cache() -> None:
    global _probe_cache
    _probe_cache = _PROBE_SENTINEL


def _default_agent_base() -> str:
    host = os.environ.get("VDISPLAY_AGENT_HOST", "127.0.0.1").strip() or "127.0.0.1"
    port = os.environ.get("VDISPLAY_AGENT_PORT", "8765").strip() or "8765"
    return f"http://{host}:{port}"


def _is_vdisplay_agent_health(payload: object) -> bool:
    """Reject lookalike /health responders (e.g. other localhost brokers on 8765)."""
    if not isinstance(payload, dict):
        return False
    if payload.get("ok") is not True:
        return False
    data = payload.get("data")
    if not isinstance(data, dict):
        return False
    service = str(data.get("service") or data.get("broker") or "").strip().lower()
    return service == "vdisplay-agent"


def _probe_agent_url(base_url: str, *, timeout: float = 0.2) -> str | None:
    try:
        with urllib.request.urlopen(f"{base_url.rstrip('/')}/health", timeout=timeout) as response:
            if response.status != 200:
                return None
            raw = response.read()
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return None
    try:
        import json

        payload = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    if _is_vdisplay_agent_health(payload):
        return base_url.rstrip("/")
    return None


def _probe_default_agent() -> str | None:
    global _probe_cache
    if isinstance(_probe_cache, str):
        return _probe_cache
    url = _probe_agent_url(_default_agent_base())
    if url:
        _probe_cache = url
    return url


def resolve_agent_url(explicit: str | None = None, *, allow_auto: bool = False) -> str | None:
    """Return agent base URL when clients should use IPC instead of in-process capture."""
    url = (explicit or os.environ.get("VDISPLAY_AGENT_URL") or "").strip()
    if url:
        return url.rstrip("/")
    if not allow_auto or not agent_auto_enabled():
        return None
    return _probe_default_agent()


def resolve_agent_token() -> str | None:
    token = (os.environ.get("VDISPLAY_AGENT_TOKEN") or "").strip()
    return token or None


def use_agent(explicit: str | None = None) -> bool:
    if os.environ.get("VDISPLAY_AGENT_BROKER", "").strip().lower() in {"1", "true", "yes"}:
        return False
    return resolve_agent_url(explicit, allow_auto=True) is not None
