"""Post-action settle delay before verify."""

from __future__ import annotations

import pytest

from vdisplay.application.services import control as control_svc
from vdisplay.control.providers.terminal_session import default_registry


def test_control_settle_seconds_zero_without_verify() -> None:
    assert control_svc._control_settle_seconds(verify=False, screenshot_verify=False) == 0.0


def test_control_settle_seconds_default_with_verify(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VDISPLAY_CONTROL_SETTLE_MS", raising=False)
    assert control_svc._control_settle_seconds(verify=True, screenshot_verify=False) == 0.15


def test_control_settle_seconds_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_CONTROL_SETTLE_MS", "0")
    assert control_svc._control_settle_seconds(verify=True, screenshot_verify=False) == 0.0


def test_terminal_set_value_verify_with_settle_env(monkeypatch: pytest.MonkeyPatch) -> None:
    default_registry().close_all()
    default_registry().open_mock(session_id="demo", lines=[""], cursor_row=0, cursor_col=0)
    settle_calls: list[float] = []
    orig_settle = control_svc._control_settle_seconds

    def _track_settle(**kwargs: object) -> float:
        value = orig_settle(**{k: v for k, v in kwargs.items()})  # type: ignore[arg-type]
        settle_calls.append(value)
        return value

    monkeypatch.setattr(control_svc, "_control_settle_seconds", _track_settle)
    monkeypatch.setenv("VDISPLAY_CONTROL_SETTLE_MS", "200")

    result = control_svc._execute_action(
        action="set_value",
        display=None,
        backend="terminal",
        verify=True,
        screenshot_verify=False,
        value="hello",
        session_id="demo",
        environment="terminal",
        role="input",
    )
    assert result["verified"] is True
    assert settle_calls == [0.2]
    default_registry().close_all()
