from __future__ import annotations

import pytest

from vdisplay.control.descriptors import BUILTIN_PROVIDER_DESCRIPTORS, extension_catalog
from vdisplay.control.models import EnvironmentKind
from vdisplay.control.policy import evaluate_provider_routing
from vdisplay.control.profile_inference import infer_application_profile
from vdisplay.control.providers.vision import VisionStubProvider
from vdisplay.control.routing_semantics import build_routing_semantics, requires_open_session
from vdisplay.control.scoring import rank_providers
from vdisplay.control.selector import ControlSelector


def _mock_readiness(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("vdisplay.control.scoring._atspi_ready", lambda: (True, "atspi ok"))
    monkeypatch.setattr("vdisplay.control.scoring._browser_ready", lambda: (True, "browser ok"))
    monkeypatch.setattr("vdisplay.control.scoring._xdotool_ready", lambda: (True, "xdotool ok"))
    monkeypatch.setattr("vdisplay.control.scoring._terminal_ready", lambda: (True, "terminal ok"))
    monkeypatch.setattr("vdisplay.control.scoring._vision_ready", lambda: (True, "vision stub ok"))
    monkeypatch.setattr(
        "vdisplay.control.scoring._browser_session_ready",
        lambda _sid: (True, "browser session ok"),
    )
    monkeypatch.setattr(
        "vdisplay.control.scoring._terminal_session_ready",
        lambda _sid: (True, "terminal session ok"),
    )


def test_vision_stub_provider_available() -> None:
    provider = VisionStubProvider()
    ok, reason = provider.available()
    assert ok is True
    assert "vision" in reason


def test_vision_stub_find_by_anchor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "vdisplay.control.providers.vision.provider.ocr_available",
        lambda: (False, "pytesseract not installed"),
    )
    provider = VisionStubProvider()
    nodes = provider.find(ControlSelector(vision_anchor="login-button"))
    assert len(nodes) == 1
    assert nodes[0].name == "login-button"
    assert nodes[0].state.get("stub") is True


def test_builtin_provider_count_no_per_engine_explosion() -> None:
    catalog = extension_catalog()
    provider_ids = sorted(item["provider_id"] for item in catalog["providers"])
    assert provider_ids == ["atspi", "ax", "browser", "terminal", "uia", "vision", "x11"]
    assert len(BUILTIN_PROVIDER_DESCRIPTORS) == 7
    assert "browser_firefox" not in provider_ids
    assert "browser_chromium" not in provider_ids


def test_infer_vision_only_surface_profile() -> None:
    inferred = infer_application_profile(ControlSelector(vision_anchor="canvas-play"))
    assert inferred is not None
    assert inferred.profile_id == "vision_only_surface"
    assert inferred.confidence >= 0.9


def test_vision_only_surface_routes_to_x11(monkeypatch: pytest.MonkeyPatch) -> None:
    """vision_only_surface → x11 fallback, not vision stub."""
    from vdisplay.control.descriptors import HostEnvironmentKind, PlatformProfile

    _mock_readiness(monkeypatch)
    monkeypatch.setattr(
        "vdisplay.control.descriptors.detect_platform_profile",
        lambda **kwargs: PlatformProfile(
            os_family="linux",
            display_stack="x11",
            host_environment=HostEnvironmentKind.LINUX_X11,
        ),
    )
    decision = evaluate_provider_routing(
        backend="auto",
        selector=ControlSelector(vision_anchor="play-btn"),
    )
    assert decision.selected_provider == "x11"
    assert decision.application_profile == "vision_only_surface"
    vision = next(item for item in decision.candidates if item.provider == "vision")
    assert vision.eligible is True
    assert any("defers auto routing" in reason for reason in vision.reasons)


def test_vision_provider_stub_anchor_without_ocr(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.control.providers.vision import VisionProviderStub

    monkeypatch.setattr(
        "vdisplay.control.providers.vision.provider.ocr_available",
        lambda: (False, "pytesseract not installed"),
    )
    provider = VisionProviderStub()
    assert provider.name == "vision"
    nodes = provider.find(ControlSelector(vision_anchor="test"))
    assert len(nodes) == 1
    assert nodes[0].id == "vision:test"
    result = provider.invoke(nodes[0].id)
    assert result["ok"] is False
    assert result.get("stub") is True


def test_routing_semantics_vision_requires_no_session() -> None:
    semantics = build_routing_semantics(selector=ControlSelector(vision_anchor="btn"))
    assert semantics.target_environment == EnvironmentKind.VISION
    assert semantics.session_kind is None
    assert semantics.requires_open_session is False
    assert requires_open_session(EnvironmentKind.VISION) is False
    assert "screenshot" in semantics.legal_verify_modes


def test_vision_routing_on_wayland_host(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.control.descriptors import HostEnvironmentKind, PlatformProfile

    _mock_readiness(monkeypatch)
    monkeypatch.setattr(
        "vdisplay.control.descriptors.detect_platform_profile",
        lambda **kwargs: PlatformProfile(
            os_family="linux",
            display_stack="wayland",
            host_environment=HostEnvironmentKind.LINUX_WAYLAND,
            security_constraints=["xdotool ineffective on Wayland"],
        ),
    )
    monkeypatch.setattr(
        "vdisplay.control.scoring._xwayland_reachable",
        lambda display=None: (False, "X display not reachable"),
    )

    decision = evaluate_provider_routing(
        backend="auto",
        selector=ControlSelector(vision_anchor="game-ui"),
    )
    assert decision.selected_provider == "vision"
    x11 = next(item for item in decision.candidates if item.provider == "x11")
    assert x11.eligible is False
    vision = next(item for item in decision.candidates if item.provider == "vision")
    assert vision.eligible is True


def test_x11_fallback_boost_for_vision_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.control.descriptors import HostEnvironmentKind, PlatformProfile

    _mock_readiness(monkeypatch)
    monkeypatch.setattr(
        "vdisplay.control.descriptors.detect_platform_profile",
        lambda **kwargs: PlatformProfile(
            os_family="linux",
            display_stack="x11",
            host_environment=HostEnvironmentKind.LINUX_X11,
        ),
    )
    ranked, inference = rank_providers(selector=ControlSelector(vision_anchor="btn"))
    assert inference is not None
    assert inference["profile_id"] == "vision_only_surface"
    assert ranked[0].provider == "x11"
    x11 = next(item for item in ranked if item.provider == "x11")
    assert x11.eligible is True
    assert any("primary provider for profile vision_only_surface" in reason for reason in x11.reasons)
