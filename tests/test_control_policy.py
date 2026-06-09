from __future__ import annotations

import pytest

from vdisplay.control.policy import assess_control_capability


def test_assess_control_capability_returns_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "vdisplay.control.policy._atspi_ready",
        lambda: (False, "gi missing in test"),
    )
    monkeypatch.setattr(
        "vdisplay.control.policy._xdotool_ready",
        lambda: (True, "xdotool available"),
    )
    contract = assess_control_capability()
    assert contract.fallback_to_pointer_injection is True
    assert "x11-fallback" in contract.backends
    assert contract.supports_semantic_control is False
