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
    from vdisplay.capture.portal_screencast import get_active_screencast

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
    payload["capabilities"] = platform_capabilities()
    return payload
