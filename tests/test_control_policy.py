from __future__ import annotations

import pytest

from vdisplay.control.policy import assess_control_capability


def test_assess_control_capability_returns_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.control.descriptors import HostEnvironmentKind, PlatformProfile

    monkeypatch.setattr(
        "vdisplay.control.descriptors.detect_platform_profile",
        lambda **kwargs: PlatformProfile(
            os_family="linux",
            display_stack="x11",
            host_environment=HostEnvironmentKind.LINUX_X11,
        ),
    )
    monkeypatch.setattr(
        "vdisplay.control.policy._atspi_ready",
        lambda: (False, "gi missing in test"),
    )
    monkeypatch.setattr(
        "vdisplay.control.policy._xdotool_ready",
        lambda: (True, "xdotool available"),
    )
    monkeypatch.setattr(
        "vdisplay.control.policy._terminal_ready",
        lambda: (False, "terminal unavailable in test"),
    )
    monkeypatch.setattr(
        "vdisplay.control.policy._browser_ready",
        lambda: (False, "browser unavailable in test"),
    )
    contract = assess_control_capability()
    assert contract.fallback_to_pointer_injection is True
    assert "x11-fallback" in contract.backends
    assert contract.supports_semantic_control is False
