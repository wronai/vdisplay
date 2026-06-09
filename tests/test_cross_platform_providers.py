"""PR-19 — Windows UIA / macOS AX provider stubs + host-gated routing."""

from __future__ import annotations

import pytest

from vdisplay.control.descriptors import (
    BUILTIN_PROVIDER_DESCRIPTORS,
    HostEnvironmentKind,
    PlatformProfile,
    extension_catalog,
)
from vdisplay.control.policy import evaluate_provider_routing
from vdisplay.control.profile_inference import infer_application_profile
from vdisplay.control.models import ControlBounds, ControlRole
from vdisplay.control.providers.ax import AxStubProvider
from vdisplay.control.providers.uia import UiaStubProvider
from vdisplay.control.selector import ControlSelector


def _mock_linux_readiness(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("vdisplay.control.scoring._atspi_ready", lambda: (True, "atspi ok"))
    monkeypatch.setattr("vdisplay.control.scoring._uia_ready", lambda: (False, "uia requires Windows host"))
    monkeypatch.setattr("vdisplay.control.scoring._ax_ready", lambda: (False, "ax requires macOS host"))
    monkeypatch.setattr("vdisplay.control.scoring._browser_ready", lambda: (True, "browser ok"))
    monkeypatch.setattr("vdisplay.control.scoring._xdotool_ready", lambda: (True, "x11 ok"))
    monkeypatch.setattr("vdisplay.control.scoring._terminal_ready", lambda: (True, "terminal ok"))
    monkeypatch.setattr("vdisplay.control.scoring._vision_ready", lambda: (True, "vision ok"))
    monkeypatch.setattr(
        "vdisplay.control.scoring._browser_session_ready",
        lambda _sid: (True, "browser session ok"),
    )
    monkeypatch.setattr(
        "vdisplay.control.scoring._terminal_session_ready",
        lambda _sid: (True, "terminal session ok"),
    )


def _mock_platform(
    monkeypatch: pytest.MonkeyPatch,
    *,
    os_family: str,
    display_stack: str,
    host: HostEnvironmentKind,
) -> None:
    monkeypatch.setattr(
        "vdisplay.control.descriptors.detect_platform_profile",
        lambda **kwargs: PlatformProfile(
            os_family=os_family,
            display_stack=display_stack,
            host_environment=host,
        ),
    )


def test_builtin_provider_count_includes_cross_platform_stubs() -> None:
    catalog = extension_catalog()
    provider_ids = sorted(item["provider_id"] for item in catalog["providers"])
    assert provider_ids == ["atspi", "ax", "browser", "terminal", "uia", "vision", "x11"]
    assert len(BUILTIN_PROVIDER_DESCRIPTORS) == 7


def test_uia_stub_unavailable_on_linux() -> None:
    provider = UiaStubProvider()
    ok, reason = provider.available()
    assert ok is False
    assert "Windows" in reason


def test_ax_stub_unavailable_on_linux() -> None:
    provider = AxStubProvider()
    ok, reason = provider.available()
    assert ok is False
    assert "macOS" in reason


def test_linux_desktop_routes_atspi_not_uia_or_ax(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_linux_readiness(monkeypatch)
    _mock_platform(
        monkeypatch,
        os_family="linux",
        display_stack="x11",
        host=HostEnvironmentKind.LINUX_X11,
    )

    decision = evaluate_provider_routing(
        backend="auto",
        selector=ControlSelector(role="button", name="OK"),
    )
    assert decision.selected_provider == "atspi"
    uia = next(item for item in decision.candidates if item.provider == "uia")
    ax = next(item for item in decision.candidates if item.provider == "ax")
    assert uia.eligible is False
    assert ax.eligible is False


def test_windows_desktop_routes_uia(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_linux_readiness(monkeypatch)
    monkeypatch.setattr("vdisplay.control.scoring._uia_ready", lambda: (True, "uia stub ready"))
    _mock_platform(
        monkeypatch,
        os_family="windows",
        display_stack="x11",
        host=HostEnvironmentKind.WINDOWS,
    )

    decision = evaluate_provider_routing(
        backend="auto",
        selector=ControlSelector(role="button", accessibility_id="ok-btn"),
    )
    assert decision.selected_provider == "uia"
    assert decision.application_profile == "native_windows"
    atspi = next(item for item in decision.candidates if item.provider == "atspi")
    assert atspi.eligible is False


def test_macos_desktop_routes_ax(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_linux_readiness(monkeypatch)
    monkeypatch.setattr("vdisplay.control.scoring._ax_ready", lambda: (True, "ax stub ready"))
    _mock_platform(
        monkeypatch,
        os_family="darwin",
        display_stack="x11",
        host=HostEnvironmentKind.DARWIN,
    )

    decision = evaluate_provider_routing(
        backend="auto",
        selector=ControlSelector(role="button", app="Safari"),
    )
    assert decision.selected_provider == "ax"
    assert decision.application_profile == "native_macos"
    atspi = next(item for item in decision.candidates if item.provider == "atspi")
    assert atspi.eligible is False


def test_native_windows_profile_only_on_windows_host(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_platform(
        monkeypatch,
        os_family="linux",
        display_stack="x11",
        host=HostEnvironmentKind.LINUX_X11,
    )
    inference = infer_application_profile(ControlSelector(role="button"))
    assert inference is not None
    assert inference.profile_id == "native_gtk"

    _mock_platform(
        monkeypatch,
        os_family="windows",
        display_stack="x11",
        host=HostEnvironmentKind.WINDOWS,
    )
    inference = infer_application_profile(ControlSelector(role="button"))
    assert inference is not None
    assert inference.profile_id == "native_windows"


def test_uia_find_by_accessibility_id() -> None:
    from vdisplay.control.providers.uia import UiaControlProvider
    from vdisplay.control.providers.uia_impl import MockUiaBackend, UiaElementRecord

    backend = MockUiaBackend(
        [
            UiaElementRecord(
                key="1",
                name="submit",
                role=ControlRole.BUTTON,
                bounds=ControlBounds(x=1, y=2, width=10, height=10),
                automation_id="submit",
                provider_ref="submit",
            )
        ]
    )
    provider = UiaControlProvider(backend=backend)
    nodes = provider.find(ControlSelector(accessibility_id="submit"))
    assert len(nodes) == 1
    assert nodes[0].provider_ref == "submit"
