"""Platform and capability info use-case."""

from __future__ import annotations

from typing import Any

from ...api import MirrorSession, VirtualDisplaySession, WindowRelaySession, platform_summary
from ...discovery import list_outputs
from ...exceptions import VDisplayError


def platform_info() -> dict[str, Any]:
    from ...capture.linux_xwd import _is_wayland_session

    session = VirtualDisplaySession.create(backend="xvfb")
    payload: dict[str, Any] = {
        "platform": platform_summary(),
        "virtual_capabilities": session.capabilities(),
        "mirror_capabilities": MirrorSession.create().capabilities(),
        "relay_capabilities": WindowRelaySession.create().capabilities(),
    }
    try:
        payload["monitors"] = list_outputs()
    except VDisplayError:
        payload["monitors"] = []
    if _is_wayland_session():
        payload["session_type"] = "wayland"
        payload["host_capture_hint"] = (
            "Wayland host capture needs vdisplay-agent + ScreenCast: "
            "vdisplay agent serve, then vdisplay agent screencast start"
        )
        try:
            from ...agent_config import resolve_agent_url
            from ...client import AgentClient

            url = resolve_agent_url(allow_auto=True)
            if url:
                screencast = AgentClient(url).screencast_status()
                payload["agent"] = {
                    "url": url,
                    "screencast_active": bool(screencast.get("active")),
                    "screencast_ready": bool(screencast.get("ready")),
                }
                if not screencast.get("ready"):
                    payload["host_capture_hint"] += (
                        " (screencast not ready — run: vdisplay agent screencast start)"
                    )
        except VDisplayError:
            payload["agent"] = {"url": None, "screencast_ready": False}
            payload["host_capture_hint"] += " (agent not reachable — run: vdisplay agent serve)"
    return payload
