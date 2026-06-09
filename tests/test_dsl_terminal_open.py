from __future__ import annotations

import pytest

from dsl2vdisplay.bus import dispatch
from dsl2vdisplay.grammar import parse_line
from vdisplay.application.commands import CommandRequest, CommandResult, CommandVerb
from vdisplay.control.providers.terminal_session import default_registry


def test_parse_terminal_open_line() -> None:
    cmd = parse_line('terminal open --session-id demo --rows 30 --cols 100')
    assert cmd is not None
    assert cmd["verb"] == "TERMINAL_OPEN"
    assert cmd["session_id"] == "demo"
    assert cmd["rows"] == 30
    assert cmd["cols"] == 100


def test_command_request_from_dsl_terminal_open() -> None:
    cmd = parse_line('terminal open --session-id t1 --command "bash -i"')
    assert cmd is not None
    request = CommandRequest.from_dsl(cmd, line="terminal open")
    assert request.verb == CommandVerb.TERMINAL_OPEN
    assert request.terminal_session_id == "t1"
    assert request.terminal_command == "bash -i"


def test_dispatch_terminal_open_local(monkeypatch: pytest.MonkeyPatch) -> None:
    opened: dict[str, object] = {}

    def fake_terminal_open(**kwargs):
        opened.update(kwargs)
        return {"ok": True, "session_id": kwargs.get("session_id") or "auto", "mode": "terminal"}

    monkeypatch.setattr(
        "vdisplay.application.services.session.terminal_open",
        fake_terminal_open,
    )

    result = dispatch('terminal open --session-id dsl-demo')
    assert result.ok is True
    assert result.action == "terminal_open"
    assert opened["session_id"] == "dsl-demo"


def test_terminal_open_e2e_local() -> None:
    default_registry().close_all()
    try:
        result = dispatch("terminal open --session-id e2e-term")
        assert result.ok is True
        assert result.data["session_id"] == "e2e-term"
        assert default_registry().get("e2e-term") is not None
    finally:
        default_registry().close_all()


def test_dispatch_terminal_open_via_executor(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_execute(request, **kwargs):
        assert request.verb == CommandVerb.TERMINAL_OPEN
        return CommandResult.success(action="terminal_open", data={"session_id": "x"})

    import vdisplay.application.executor as executor_mod

    monkeypatch.setattr(executor_mod, "execute", fake_execute)
    result = dispatch("terminal open --session-id x")
    assert result.ok is True
    assert result.action == "terminal_open"
