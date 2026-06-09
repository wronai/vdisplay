"""Platform and capability info use-case."""

from __future__ import annotations

from typing import Any

from ...api import MirrorSession, VirtualDisplaySession, WindowRelaySession, platform_summary
from ...discovery import list_outputs
from ...exceptions import VDisplayError


def platform_info() -> dict[str, Any]:
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
    return payload
