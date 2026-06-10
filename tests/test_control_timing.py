"""Control timing helpers for focus and pointer settle."""

from __future__ import annotations

import pytest

from vdisplay.control.timing import control_focus_type_seconds, control_pointer_settle_seconds


def test_control_focus_type_seconds_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VDISPLAY_CONTROL_FOCUS_MS", raising=False)
    assert control_focus_type_seconds() == 0.35


def test_control_focus_type_seconds_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_CONTROL_FOCUS_MS", "100")
    assert control_focus_type_seconds() == 0.1


def test_control_pointer_settle_seconds_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VDISPLAY_CONTROL_POINTER_SETTLE_MS", raising=False)
    assert control_pointer_settle_seconds() == 0.05


def test_control_pointer_settle_seconds_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_CONTROL_POINTER_SETTLE_MS", "0")
    assert control_pointer_settle_seconds() == 0.0
