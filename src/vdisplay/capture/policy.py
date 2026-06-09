"""Capture policy and unattended capability contract."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from ..discovery import _looks_like_xvfb_only, resolve_host_display
from .linux_xwd import _is_wayland_session

CaptureMode = Literal["unattended", "best-effort", "low-latency", "desktop", "strict"]
RecommendedProfile = Literal["virtual", "screencast", "driver", "unsupported"]


@dataclass(frozen=True)
class CaptureCapabilityContract:
    """Whether this host can do prompt-free continuous capture."""

    supports_unattended_capture: bool
    requires_user_consent: bool
    supports_persistent_restore: bool
    capture_latency_class: Literal["low", "medium", "high"]
    safe_polling_hz: float
    recommended_profile: RecommendedProfile
    recommended_mode: CaptureMode
    session_type: Literal["wayland", "x11", "virtual"]
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def assess_unattended_capture(
    *,
    display: str | None = None,
    agent_url: str | None = None,
    screencast_ready: bool | None = None,
) -> CaptureCapabilityContract:
    if display and _looks_like_xvfb_only(display):
        return _assess_virtual(f"explicit virtual display {display} — xwd capture without portal")

    resolved = resolve_host_display(display or os.environ.get("DISPLAY"))
    if _looks_like_xvfb_only(resolved):
        return _assess_virtual("owned Xvfb display — xwd capture without portal")

    if _is_wayland_session():
        return _assess_wayland(agent_url, screencast_ready)

    return CaptureCapabilityContract(
        supports_unattended_capture=True,
        requires_user_consent=False,
        supports_persistent_restore=True,
        capture_latency_class="low",
        safe_polling_hz=5.0,
        recommended_profile="driver",
        recommended_mode="best-effort",
        session_type="x11",
        reasons=["pure X11 — driver chain may work without portal"],
    )


def _assess_virtual(reason: str) -> CaptureCapabilityContract:
    return CaptureCapabilityContract(
        supports_unattended_capture=True,
        requires_user_consent=False,
        supports_persistent_restore=True,
        capture_latency_class="low",
        safe_polling_hz=10.0,
        recommended_profile="virtual",
        recommended_mode="strict",
        session_type="virtual",
        reasons=[reason],
    )


def _assess_wayland(agent_url: str | None, screencast_ready: bool | None) -> CaptureCapabilityContract:
    ready = screencast_ready
    if ready is None:
        try:
            from .portal_screencast import get_active_screencast
            session = get_active_screencast()
            if session is not None and session.is_ready:
                ready = True
        except Exception:
            pass
    if ready is None and agent_url:
        try:
            from ..client import AgentClient
            status = AgentClient(agent_url).screencast_status()
            ready = bool(status.get("active") and status.get("ready"))
        except Exception:
            ready = False
    ready = bool(ready)

    if ready:
        return CaptureCapabilityContract(
            supports_unattended_capture=True,
            requires_user_consent=False,
            supports_persistent_restore=False,
            capture_latency_class="medium",
            safe_polling_hz=2.0,
            recommended_profile="screencast",
            recommended_mode="desktop",
            session_type="wayland",
            reasons=[
                "active ScreenCast session — loop capture without new portal prompts",
                "restart screencast after agent serve or blank frame",
            ],
        )

    reasons = [
        "GNOME Wayland host — driver/DRM capture usually blank on NVIDIA",
        "one-time portal consent required: vdisplay agent screencast start",
    ]
    if not agent_url:
        reasons.append("agent not reachable — run: vdisplay agent serve")

    return CaptureCapabilityContract(
        supports_unattended_capture=False,
        requires_user_consent=True,
        supports_persistent_restore=False,
        capture_latency_class="high",
        safe_polling_hz=1.0,
        recommended_profile="screencast",
        recommended_mode="desktop",
        session_type="wayland",
        reasons=reasons,
    )
