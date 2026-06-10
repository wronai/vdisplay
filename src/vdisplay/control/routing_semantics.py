"""Host/target/session/verify semantics for routing and diagnostics."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .descriptors import HostEnvironmentKind, PlatformProfile, detect_platform_profile
from .models import EnvironmentKind
from .selector import ControlSelector
from .session_kind import SessionKind
from .verify_strategy import VerifyStrategy


@dataclass(frozen=True)
class RoutingSemantics:
    """Unified routing contract: host, target, session, verify."""

    host_environment: HostEnvironmentKind
    target_environment: EnvironmentKind
    session_kind: SessionKind | None
    requires_open_session: bool
    legal_verify_modes: tuple[str, ...]
    host_constraints: list[str] = field(default_factory=list)
    platform: PlatformProfile | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "host_environment": self.host_environment.value,
            "target_environment": self.target_environment.value,
            "session_kind": self.session_kind.value if self.session_kind else None,
            "requires_open_session": self.requires_open_session,
            "legal_verify_modes": list(self.legal_verify_modes),
            "host_constraints": list(self.host_constraints),
        }
        if self.platform is not None:
            payload["platform"] = self.platform.to_dict()
        return payload


_HOST_CONSTRAINTS: dict[HostEnvironmentKind, list[str]] = {
    HostEnvironmentKind.LINUX_WAYLAND: [
        "xdotool ineffective on Wayland — use AT-SPI or browser session",
        "capture may require portal screencast for unattended desktop frames",
    ],
    HostEnvironmentKind.LINUX_HEADLESS: [
        "no interactive desktop — virtual display or session-scoped providers",
    ],
    HostEnvironmentKind.WINDOWS: [
        "desktop semantic control via uia provider (atspi/x11 not applicable)",
    ],
    HostEnvironmentKind.DARWIN: [
        "desktop semantic control via ax provider (atspi/x11 not applicable)",
    ],
}

_TARGET_SESSION_KIND: dict[EnvironmentKind, SessionKind] = {
    EnvironmentKind.BROWSER: SessionKind.BROWSER,
    EnvironmentKind.TERMINAL: SessionKind.TERMINAL,
}

_TARGET_VERIFY_MODES: dict[EnvironmentKind, tuple[VerifyStrategy, ...]] = {
    EnvironmentKind.DESKTOP: (
        VerifyStrategy.STRUCTURE,
        VerifyStrategy.TEXT,
        VerifyStrategy.SCREENSHOT,
        VerifyStrategy.HYBRID,
    ),
    EnvironmentKind.BROWSER: (
        VerifyStrategy.DOM,
        VerifyStrategy.STRUCTURE,
        VerifyStrategy.TEXT,
        VerifyStrategy.HYBRID,
    ),
    EnvironmentKind.TERMINAL: (
        VerifyStrategy.TEXT,
        VerifyStrategy.STRUCTURE,
        VerifyStrategy.HYBRID,
    ),
    EnvironmentKind.VISION: (
        VerifyStrategy.SCREENSHOT,
        VerifyStrategy.OCR,
        VerifyStrategy.ANCHOR_VISIBLE,
    ),
    EnvironmentKind.MOBILE: (VerifyStrategy.STRUCTURE, VerifyStrategy.SCREENSHOT),
}


def host_environment_constraints(host: HostEnvironmentKind) -> list[str]:
    return list(_HOST_CONSTRAINTS.get(host, ()))


def infer_target_environment(
    selector: ControlSelector | None,
    *,
    session_id: str | None = None,
) -> EnvironmentKind:
    from .scoring import selector_context

    if selector is None:
        selector = ControlSelector()
    ctx = selector_context(selector, session_id)
    if ctx["browser"]:
        return EnvironmentKind.BROWSER
    if ctx["terminal"]:
        return EnvironmentKind.TERMINAL
    if ctx["vision"]:
        return EnvironmentKind.VISION
    if selector.environment:
        try:
            return EnvironmentKind(selector.environment)
        except ValueError:
            pass
    return EnvironmentKind.DESKTOP


def session_kind_for_target(target: EnvironmentKind) -> SessionKind | None:
    return _TARGET_SESSION_KIND.get(target)


def legal_verify_modes_for_target(target: EnvironmentKind) -> tuple[str, ...]:
    modes = _TARGET_VERIFY_MODES.get(target, (VerifyStrategy.STRUCTURE,))
    return tuple(mode.value for mode in modes)


def requires_open_session(target: EnvironmentKind) -> bool:
    return target in {EnvironmentKind.BROWSER, EnvironmentKind.TERMINAL}


def build_routing_semantics(
    *,
    selector: ControlSelector | None = None,
    session_id: str | None = None,
    display: str | None = None,
) -> RoutingSemantics:
    platform = detect_platform_profile(display=display)
    target = infer_target_environment(selector, session_id=session_id)
    session_kind = session_kind_for_target(target)
    constraints = host_environment_constraints(platform.host_environment)
    constraints.extend(platform.security_constraints)
    return RoutingSemantics(
        host_environment=platform.host_environment,
        target_environment=target,
        session_kind=session_kind,
        requires_open_session=requires_open_session(target),
        legal_verify_modes=legal_verify_modes_for_target(target),
        host_constraints=constraints,
        platform=platform,
    )


def host_environment_from_capture_session_type(session_type: str) -> HostEnvironmentKind:
    mapping = {
        "wayland": HostEnvironmentKind.LINUX_WAYLAND,
        "x11": HostEnvironmentKind.LINUX_X11,
        "virtual": HostEnvironmentKind.LINUX_HEADLESS,
    }
    return mapping.get(session_type, HostEnvironmentKind.UNKNOWN)
