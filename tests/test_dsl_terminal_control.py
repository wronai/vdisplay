from __future__ import annotations

import pytest

from dsl2vdisplay import dispatch
from vdisplay.application.commands import CommandRequest, CommandResult
from vdisplay.control.providers.terminal_session import default_registry


def test_dsl_terminal_set_value_end_to_end(monkeypatch: pytest.MonkeyPatch) -> None:
    default_registry().close_all()
    default_registry().open_mock(session_id="demo", lines=[""], cursor_row=0, cursor_col=0)

    captured: list[CommandRequest] = []

    def fake_execute(request: CommandRequest, **kwargs):
        captured.append(request)
        from vdisplay.application.handlers import local as local_handlers

        handler = local_handlers._LOCAL_HANDLERS[request.verb]
        data = handler(request)
        return CommandResult.success(action=request.action, data=data)

    import vdisplay.application.executor as executor_mod

    monkeypatch.setattr(executor_mod, "execute", fake_execute)

    result = dispatch(
        "control set-value --backend terminal --session-id demo "
        "--environment terminal --role input --value hello --verify"
    )
    assert result.ok is True
    assert len(captured) == 1
    request = captured[0]
    assert request.control_backend == "terminal"
    assert request.control_session_id == "demo"
    assert request.control_environment == "terminal"
    assert request.control_value == "hello"
    assert request.control_verify is True
    assert result.data.get("verified") is True
    default_registry().close_all()
