from __future__ import annotations

import pytest

from vdisplay.application.runtime import get_execution_policy
from vdisplay.application.services import control as control_svc
from vdisplay.application.services.discovery import diagnose_unattended
from vdisplay.capture.policy import assess_unattended_capture
from vdisplay.control.descriptors import HostEnvironmentKind
from vdisplay.control.models import EnvironmentKind
from vdisplay.control.policy import assess_control_capability, evaluate_provider_routing
from vdisplay.control.routing_semantics import (
    build_routing_semantics,
    infer_target_environment,
    requires_open_session,
)
from vdisplay.control.scoring import rank_providers
from vdisplay.control.selector import ControlSelector
from vdisplay.control.session_kind import SessionKind


def test_infer_target_environment_mapping() -> None:
    assert infer_target_environment(ControlSelector(dom_css="#go")) == EnvironmentKind.BROWSER
    assert infer_target_environment(
        ControlSelector(environment="terminal", session_id="t1"),
        session_id="t1",
    ) == EnvironmentKind.TERMINAL
    assert infer_target_environment(ControlSelector(role="button")) == EnvironmentKind.DESKTOP


def test_build_routing_semantics_browser_requires_session() -> None:
    semantics = build_routing_semantics(selector=ControlSelector(dom_css="#submit"))
    assert semantics.target_environment == EnvironmentKind.BROWSER
    assert semantics.session_kind == SessionKind.BROWSER
    assert semantics.requires_open_session is True
    assert "dom" in semantics.legal_verify_modes
    assert semantics.host_environment in HostEnvironmentKind


def test_build_routing_semantics_vision_anchor_visible() -> None:
    semantics = build_routing_semantics(
        selector=ControlSelector(vision_anchor="Play", environment="vision"),
    )
    assert semantics.target_environment == EnvironmentKind.VISION
    assert "anchor_visible" in semantics.legal_verify_modes
    assert "ocr" in semantics.legal_verify_modes


def test_x11_provider_ineligible_on_wayland_host_without_xwayland(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.control.descriptors import PlatformProfile

    monkeypatch.setattr(
        "vdisplay.control.descriptors.detect_platform_profile",
        lambda **kwargs: PlatformProfile(
            os_family="linux",
            display_stack="wayland",
            host_environment=HostEnvironmentKind.LINUX_WAYLAND,
            security_constraints=["xdotool ineffective on Wayland"],
        ),
    )
    monkeypatch.setattr("vdisplay.control.scoring._xdotool_ready", lambda: (True, "xdotool available"))
    monkeypatch.setattr(
        "vdisplay.control.scoring._xwayland_reachable",
        lambda display=None: (False, "X display :0 not reachable"),
    )
    monkeypatch.setattr("vdisplay.control.scoring._atspi_ready", lambda: (True, "atspi ok"))
    monkeypatch.setattr("vdisplay.control.scoring._browser_ready", lambda: (True, "browser ok"))
    monkeypatch.setattr("vdisplay.control.scoring._terminal_ready", lambda: (True, "terminal ok"))
    monkeypatch.setattr(
        "vdisplay.control.scoring._browser_session_ready",
        lambda _sid: (True, "browser session ok"),
    )
    monkeypatch.setattr(
        "vdisplay.control.scoring._terminal_session_ready",
        lambda _sid: (True, "terminal session ok"),
    )

    ranked, _ = rank_providers(selector=ControlSelector(role="button"))
    x11 = next(item for item in ranked if item.provider == "x11")
    assert x11.eligible is False
    assert any("Wayland" in item for item in x11.missing_requirements)


def test_x11_provider_eligible_on_wayland_host_with_xwayland(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.control.descriptors import PlatformProfile

    monkeypatch.setattr(
        "vdisplay.control.descriptors.detect_platform_profile",
        lambda **kwargs: PlatformProfile(
            os_family="linux",
            display_stack="wayland",
            host_environment=HostEnvironmentKind.LINUX_WAYLAND,
            security_constraints=["xdotool ineffective on Wayland"],
        ),
    )
    monkeypatch.setattr("vdisplay.control.scoring._xdotool_ready", lambda: (True, "xdotool available"))
    monkeypatch.setattr(
        "vdisplay.control.scoring._xwayland_reachable",
        lambda display=None: (True, "XWayland reachable on :0"),
    )
    monkeypatch.setattr("vdisplay.control.scoring._atspi_ready", lambda: (True, "atspi ok"))
    monkeypatch.setattr("vdisplay.control.scoring._browser_ready", lambda: (True, "browser ok"))
    monkeypatch.setattr("vdisplay.control.scoring._terminal_ready", lambda: (True, "terminal ok"))
    monkeypatch.setattr(
        "vdisplay.control.scoring._browser_session_ready",
        lambda _sid: (True, "browser session ok"),
    )
    monkeypatch.setattr(
        "vdisplay.control.scoring._terminal_session_ready",
        lambda _sid: (True, "terminal session ok"),
    )

    ranked, _ = rank_providers(selector=ControlSelector(role="button"))
    x11 = next(item for item in ranked if item.provider == "x11")
    assert x11.eligible is True
    assert any("XWayland" in item for item in x11.reasons)


def test_routing_decision_includes_semantics(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("vdisplay.control.scoring._atspi_ready", lambda: (True, "atspi ok"))
    monkeypatch.setattr("vdisplay.control.scoring._browser_ready", lambda: (True, "browser ok"))
    monkeypatch.setattr("vdisplay.control.scoring._xdotool_ready", lambda: (True, "x11 ok"))
    monkeypatch.setattr("vdisplay.control.scoring._terminal_ready", lambda: (True, "terminal ok"))
    monkeypatch.setattr(
        "vdisplay.control.scoring._browser_session_ready",
        lambda _sid: (True, "browser session ok"),
    )
    monkeypatch.setattr(
        "vdisplay.control.scoring._terminal_session_ready",
        lambda _sid: (True, "terminal session ok"),
    )

    decision = evaluate_provider_routing(
        backend="auto",
        selector=ControlSelector(dom_css="#go"),
    )
    assert decision.routing_semantics is not None
    assert decision.routing_semantics["target_environment"] == "browser"
    assert decision.routing_semantics["requires_open_session"] is True


def test_assess_control_capability_includes_host_environment() -> None:
    contract = assess_control_capability()
    assert contract.host_environment
    assert isinstance(contract.host_constraints, list)


def test_assess_control_capability_blocks_pointer_on_wayland(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.control.descriptors import PlatformProfile

    monkeypatch.setattr(
        "vdisplay.control.descriptors.detect_platform_profile",
        lambda **kwargs: PlatformProfile(
            os_family="linux",
            display_stack="wayland",
            host_environment=HostEnvironmentKind.LINUX_WAYLAND,
        ),
    )
    monkeypatch.setattr("vdisplay.control.policy._atspi_ready", lambda: (True, "atspi ok"))
    monkeypatch.setattr("vdisplay.control.policy._browser_ready", lambda: (True, "browser ok"))
    monkeypatch.setattr("vdisplay.control.policy._xdotool_ready", lambda: (True, "xdotool ok"))
    monkeypatch.setattr("vdisplay.control.policy._terminal_ready", lambda: (True, "terminal ok"))
    monkeypatch.setattr(
        "vdisplay.control.scoring._xwayland_reachable",
        lambda display=None: (False, "X display not reachable"),
    )

    contract = assess_control_capability()
    assert contract.fallback_to_pointer_injection is False
    assert contract.host_environment == HostEnvironmentKind.LINUX_WAYLAND.value


def test_assess_control_capability_allows_pointer_via_xwayland(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.control.descriptors import PlatformProfile

    monkeypatch.setattr(
        "vdisplay.control.descriptors.detect_platform_profile",
        lambda **kwargs: PlatformProfile(
            os_family="linux",
            display_stack="wayland",
            host_environment=HostEnvironmentKind.LINUX_WAYLAND,
        ),
    )
    monkeypatch.setattr("vdisplay.control.policy._atspi_ready", lambda: (True, "atspi ok"))
    monkeypatch.setattr("vdisplay.control.policy._browser_ready", lambda: (True, "browser ok"))
    monkeypatch.setattr("vdisplay.control.policy._xdotool_ready", lambda: (True, "xdotool ok"))
    monkeypatch.setattr("vdisplay.control.policy._terminal_ready", lambda: (True, "terminal ok"))
    monkeypatch.setattr(
        "vdisplay.control.scoring._xwayland_reachable",
        lambda display=None: (True, "XWayland reachable on :0"),
    )

    contract = assess_control_capability()
    assert contract.fallback_to_pointer_injection is True
    assert any("XWayland" in reason for reason in contract.reasons)


def test_capture_policy_includes_host_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("vdisplay.capture.policy._is_wayland_session", lambda: True)
    contract = assess_unattended_capture(display=":0", screencast_ready=False)
    assert contract.host_environment == HostEnvironmentKind.LINUX_WAYLAND.value


def test_diagnose_unattended_includes_host_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "vdisplay.discovery.list_outputs",
        lambda *a, **k: [{"name": "DP-2", "primary": True}],
    )
    monkeypatch.setattr("vdisplay.capture.policy._is_wayland_session", lambda: True)
    monkeypatch.setattr("vdisplay.agent_config.resolve_agent_url", lambda **k: None)

    payload = diagnose_unattended(":0")
    assert "host_environment" in payload
    assert payload["unattended"]["host_environment"] == HostEnvironmentKind.LINUX_WAYLAND.value


def test_diagnose_control_includes_routing_semantics(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("vdisplay.control.scoring._atspi_ready", lambda: (True, "atspi ok"))
    monkeypatch.setattr("vdisplay.control.scoring._browser_ready", lambda: (True, "browser ok"))
    monkeypatch.setattr("vdisplay.control.scoring._xdotool_ready", lambda: (True, "x11 ok"))
    monkeypatch.setattr("vdisplay.control.scoring._terminal_ready", lambda: (True, "terminal ok"))
    monkeypatch.setattr(
        "vdisplay.control.scoring._browser_session_ready",
        lambda _sid: (True, "browser session ok"),
    )
    monkeypatch.setattr(
        "vdisplay.control.scoring._terminal_session_ready",
        lambda _sid: (True, "terminal session ok"),
    )

    payload = control_svc.diagnose_control(dom_css="#go", backend="auto")
    assert payload["routing_semantics"]["target_environment"] == "browser"
    assert requires_open_session(EnvironmentKind.BROWSER)


def test_execution_policy_meta_includes_host_environment() -> None:
    meta = get_execution_policy().meta_for("local")
    assert "host_environment" in meta
