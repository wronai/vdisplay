"""Verify policy phase selection tests."""

from __future__ import annotations

from vdisplay.control.selector import ControlSelector
from vdisplay.control.verify_policy import aggregate_confidence, required_phases


def test_required_phases_ocr_contains() -> None:
    phases = required_phases(
        action="set_value",
        verify=True,
        screenshot_verify=False,
        verify_mode="ocr_contains",
    )
    assert "ocr" in phases


def test_required_phases_hybrid() -> None:
    phases = required_phases(
        action="invoke",
        verify=True,
        screenshot_verify=True,
        verify_mode="hybrid",
    )
    assert "semantic" in phases
    assert "visual" in phases


def test_aggregate_confidence_average() -> None:
    score = aggregate_confidence(
        {
            "semantic": {"verified": True, "confidence": 0.8},
            "ocr": {"verified": True, "confidence": 1.0},
        }
    )
    assert score == 0.9
