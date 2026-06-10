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


def _evaluate_platform_backends(
    host,
    *,
    atspi_ok: bool,
    atspi_reason: str,
    uia_ok: bool,
    uia_reason: str,
    ax_ok: bool,
    ax_reason: str,
) -> tuple[list[str], list[str]]:
    from .descriptors import HostEnvironmentKind

    backends: list[str] = []
    reasons: list[str] = []
    if host in (HostEnvironmentKind.LINUX_X11, HostEnvironmentKind.LINUX_WAYLAND):
        if atspi_ok:
            backends.append("atspi")
            reasons.append(atspi_reason)
        else:
            reasons.append(f"atspi unavailable: {atspi_reason}")
    elif host == HostEnvironmentKind.WINDOWS:
        if uia_ok:
            backends.append("uia")
            reasons.append(uia_reason)
        else:
            reasons.append(f"uia unavailable: {uia_reason}")
    elif host == HostEnvironmentKind.DARWIN:
        if ax_ok:
            backends.append("ax")
            reasons.append(ax_reason)
        else:
            reasons.append(f"ax unavailable: {ax_reason}")
    return backends, reasons


def _evaluate_pointer_fallback(
    host,
    *,
    xdotool_ok: bool,
    xdotool_reason: str,
) -> tuple[list[str], list[str]]:
    from .descriptors import HostEnvironmentKind

    backends: list[str] = []
    reasons: list[str] = []
    if xdotool_ok and host == HostEnvironmentKind.LINUX_X11:
        backends.append("x11-fallback")
        reasons.append(xdotool_reason)
    elif xdotool_ok and host == HostEnvironmentKind.LINUX_WAYLAND:
        from .scoring import _xwayland_reachable

        xwayland_ok, _ = _xwayland_reachable(None)
        if xwayland_ok:
            backends.append("x11-fallback")
            reasons.append(f"{xdotool_reason} (XWayland clients)")
    return backends, reasons


def _evaluate_readiness() -> tuple[list[str], list[str], bool, bool, bool, bool, bool, bool, bool]:
    from .descriptors import HostEnvironmentKind, detect_platform_profile
    from .scoring import _ax_ready, _uia_ready

    host = detect_platform_profile().host_environment
    atspi_ok, atspi_reason = _atspi_ready()
    uia_ok, uia_reason = _uia_ready()
    ax_ok, ax_reason = _ax_ready()
    browser_ok, browser_reason = _browser_ready()
    xdotool_ok, xdotool_reason = _xdotool_ready()
    terminal_ok, terminal_reason = _terminal_ready()

    backends, reasons = _evaluate_platform_backends(
        host,
        atspi_ok=atspi_ok,
        atspi_reason=atspi_reason,
        uia_ok=uia_ok,
        uia_reason=uia_reason,
        ax_ok=ax_ok,
        ax_reason=ax_reason,
    )
    pointer_backends, pointer_reasons = _evaluate_pointer_fallback(
        host,
        xdotool_ok=xdotool_ok,
        xdotool_reason=xdotool_reason,
    )
    backends.extend(pointer_backends)
    reasons.extend(pointer_reasons)

    if browser_ok:
        backends.append("browser")
        reasons.append(browser_reason)
    else:
        reasons.append(f"browser unavailable: {browser_reason}")

    if terminal_ok:
        backends.append("terminal")
        reasons.append(terminal_reason)
    else:
        reasons.append(f"terminal unavailable: {terminal_reason}")

    semantic_ok = atspi_ok or uia_ok or ax_ok or browser_ok or terminal_ok
    return backends, reasons, semantic_ok, atspi_ok, uia_ok, ax_ok, browser_ok, xdotool_ok, terminal_ok


def _pointer_fallback_for_host(
    *,
    host,
    display: str | None,
    xdotool_ok: bool,
    reasons: list[str],
) -> bool:
    from .descriptors import HostEnvironmentKind

    if xdotool_ok and host == HostEnvironmentKind.LINUX_X11:
        return True
    if xdotool_ok and host == HostEnvironmentKind.LINUX_WAYLAND:
        from .scoring import _xwayland_reachable

        xwayland_ok, xwayland_reason = _xwayland_reachable(display)
        if xwayland_ok:
            reasons.append(f"pointer fallback via XWayland ({xwayland_reason})")
            return True
        reasons.append(f"pointer fallback blocked on linux_wayland ({xwayland_reason})")
    return False


def assess_control_capability(*, display: str | None = None) -> ControlCapabilityContract:
    from .descriptors import HostEnvironmentKind, detect_platform_profile
    from .routing_semantics import host_environment_constraints

    backends, reasons, semantic_ok, atspi_ok, uia_ok, ax_ok, browser_ok, xdotool_ok, terminal_ok = (
        _evaluate_readiness()
    )
    platform = detect_platform_profile(display=display)
    host = platform.host_environment
    host_constraints = host_environment_constraints(host)
    host_constraints.extend(platform.security_constraints)

    for env_var in ("GTK_A11Y", "QT_ACCESSIBILITY"):
        val = os.environ.get(env_var, "")
        if val:
            reasons.append(f"{env_var}={val}")

    resolve_host_display(display or os.environ.get("DISPLAY"))

    pointer_fallback = _pointer_fallback_for_host(
        host=host,
        display=display,
        xdotool_ok=xdotool_ok,
        reasons=reasons,
    )

    desktop_a11y = atspi_ok or uia_ok or ax_ok
    return ControlCapabilityContract(
        supports_semantic_control=semantic_ok,
        supports_unattended_control=desktop_a11y,
        supports_invoke=desktop_a11y or pointer_fallback or terminal_ok or browser_ok,
        supports_set_value=desktop_a11y or pointer_fallback or terminal_ok or browser_ok,
        supports_focus=desktop_a11y or pointer_fallback or terminal_ok or browser_ok,
        requires_accessibility_enablement=not desktop_a11y,
        fallback_to_pointer_injection=pointer_fallback,
        backends=backends,
        host_environment=host.value,
        reasons=reasons,
        host_constraints=host_constraints,
    )
