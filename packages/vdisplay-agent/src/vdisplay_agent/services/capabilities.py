"""Platform capabilities and diagnostics."""

from __future__ import annotations

import os
import platform
import sys
from typing import Any

from vdisplay import platform_summary
from vdisplay.capture.providers.engine import list_capture_providers
from vdisplay.discovery import diagnose_display, resolve_host_display

from ..session_store import SessionStore


def platform_capabilities() -> dict[str, Any]:
    session_type = os.environ.get("XDG_SESSION_TYPE", "unknown")
    capture_providers = list_capture_providers(resolve_host_display(None))
    from vdisplay.capture.portal_screencast import (
        ensure_portal_session_env,
        get_active_screencast,
        portal_session_env_status,
    )

    ensure_portal_session_env()
    portal_ok, portal_hint = portal_session_env_status()
    screencast = get_active_screencast()
    from vdisplay.control.policy import assess_control_capability

    control_contract = assess_control_capability()
    return {
        "platform": platform.system().lower(),
        "python": platform.python_version(),
        "session_type": session_type,
        "session_modes": ["virtual", "mirror", "relay", "terminal", "browser", "screencast", "capture_sampler"],
        "capture_sources": [row["name"] for row in capture_providers if row.get("available") == "true"],
        "capture_providers": capture_providers,
        "portal_session": {
            "ok": portal_ok,
            "hint": portal_hint or None,
            "dbus_session_bus_address": os.environ.get("DBUS_SESSION_BUS_ADDRESS"),
            "wayland_display": os.environ.get("WAYLAND_DISPLAY"),
            "xdg_runtime_dir": os.environ.get("XDG_RUNTIME_DIR"),
        },
        "screencast": {
            "supported": session_type == "wayland",
            "active": screencast is not None and screencast.active,
            "ready": screencast is not None and screencast.is_ready,
        },
        "window_relay": sys.platform.startswith("linux"),
        "input_control": sys.platform.startswith("linux"),
        "control": control_contract.to_dict(),
        "requires_admin_install": False,
        "requires_user_runtime_prompt": session_type == "wayland",
        "supports_protected_content": False,
        "task_persistence": True,
        "broker": "vdisplay-agent",
        **platform_summary(),
    }


def diagnostics(store: SessionStore, *, display: str | None = None) -> dict[str, Any]:
    resolved = resolve_host_display(display)
    payload = diagnose_display(resolved)
    payload["agent_sessions"] = len(store.sessions)
    payload["relay_active"] = store.relay is not None
    caps = platform_capabilities()
    broker_sc = store.screencast
    if broker_sc is not None:
        caps["screencast"] = {
            **caps.get("screencast", {}),
            "active": bool(broker_sc.active),
            "ready": bool(broker_sc.is_ready),
            "session_path": getattr(broker_sc, "session_path", "") or None,
            "node_ids": list(getattr(broker_sc, "node_ids", None) or []),
        }
    payload["capabilities"] = caps
    return payload
