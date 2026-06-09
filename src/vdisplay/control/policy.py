"""Control capability assessment and provider routing policy."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from typing import Any

from ..discovery import resolve_host_display
from ..exceptions import BackendNotAvailableError
from .scoring import (
    ProviderRoutingDecision,
    ProviderScore,
    _atspi_ready,
    _browser_ready,
    _terminal_ready,
    _xdotool_ready,
    normalize_backend,
    rank_providers,
    score_to_confidence,
)

__all__ = [
    "ControlCapabilityContract",
    "ProviderRoutingDecision",
    "ProviderScore",
    "assess_control_capability",
    "evaluate_provider_routing",
    "normalize_backend",
    "rank_providers",
    "score_to_confidence",
]


@dataclass(frozen=True)
class ControlCapabilityContract:
    supports_semantic_control: bool
    supports_unattended_control: bool
    supports_invoke: bool
    supports_set_value: bool
    supports_focus: bool
    requires_accessibility_enablement: bool
    fallback_to_pointer_injection: bool
    backends: list[str]
    host_environment: str
    reasons: list[str] = field(default_factory=list)
    host_constraints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_provider_routing(
    *,
    backend: str = "auto",
    selector=None,
    session_id: str | None = None,
    display: str | None = None,
    verify_semantic: bool = False,
    verify_screenshot: bool = False,
) -> ProviderRoutingDecision:
    from .router import default_router

    return default_router().evaluate(
        backend=backend,
        selector=selector,
        session_id=session_id,
        display=display,
        verify_semantic=verify_semantic,
        verify_screenshot=verify_screenshot,
    )


def _evaluate_readiness() -> tuple[list[str], list[str], bool, bool, bool, bool]:
    backends: list[str] = []
    reasons: list[str] = []

    atspi_ok, atspi_reason = _atspi_ready()
    browser_ok, browser_reason = _browser_ready()
    xdotool_ok, xdotool_reason = _xdotool_ready()
    terminal_ok, terminal_reason = _terminal_ready()

    if atspi_ok:
        backends.append("atspi")
        reasons.append(atspi_reason)
    else:
        reasons.append(f"atspi unavailable: {atspi_reason}")

    if browser_ok:
        backends.append("browser")
        reasons.append(browser_reason)
    else:
        reasons.append(f"browser unavailable: {browser_reason}")

    if xdotool_ok:
        backends.append("x11-fallback")
        reasons.append(xdotool_reason)

    if terminal_ok:
        backends.append("terminal")
        reasons.append(terminal_reason)
    else:
        reasons.append(f"terminal unavailable: {terminal_reason}")

    return backends, reasons, atspi_ok, browser_ok, xdotool_ok, terminal_ok


def assess_control_capability(*, display: str | None = None) -> ControlCapabilityContract:
    from .descriptors import HostEnvironmentKind, detect_platform_profile
    from .routing_semantics import host_environment_constraints

    backends, reasons, atspi_ok, browser_ok, xdotool_ok, terminal_ok = _evaluate_readiness()
    platform = detect_platform_profile(display=display)
    host = platform.host_environment
    host_constraints = host_environment_constraints(host)
    host_constraints.extend(platform.security_constraints)

    for env_var in ("GTK_A11Y", "QT_ACCESSIBILITY"):
        val = os.environ.get(env_var, "")
        if val:
            reasons.append(f"{env_var}={val}")

    resolve_host_display(display or os.environ.get("DISPLAY"))

    pointer_fallback = xdotool_ok and host != HostEnvironmentKind.LINUX_WAYLAND
    if xdotool_ok and host == HostEnvironmentKind.LINUX_WAYLAND:
        reasons.append("pointer fallback blocked on linux_wayland")

    return ControlCapabilityContract(
        supports_semantic_control=atspi_ok or browser_ok or terminal_ok,
        supports_unattended_control=atspi_ok,
        supports_invoke=atspi_ok or pointer_fallback or terminal_ok or browser_ok,
        supports_set_value=atspi_ok or pointer_fallback or terminal_ok or browser_ok,
        supports_focus=atspi_ok or pointer_fallback or terminal_ok or browser_ok,
        requires_accessibility_enablement=not atspi_ok,
        fallback_to_pointer_injection=pointer_fallback,
        backends=backends,
        host_environment=host.value,
        reasons=reasons,
        host_constraints=host_constraints,
    )
