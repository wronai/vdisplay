from __future__ import annotations

import pytest

from vdisplay.application.commands import CommandRequest, CommandVerb
from vdisplay.application.executor import execute
from vdisplay.application.runtime import ExecutionPolicy


def test_execution_policy_routes_to_agent_when_url_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_AGENT_URL", "http://127.0.0.1:8765")
    monkeypatch.delenv("VDISPLAY_AGENT_BROKER", raising=False)
    policy = ExecutionPolicy()
    cmd = CommandRequest(verb=CommandVerb.HEALTH)
    assert policy.route(cmd) == "agent"


def test_execution_policy_routes_local_inside_broker(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_AGENT_URL", "http://127.0.0.1:8765")
    monkeypatch.setenv("VDISPLAY_AGENT_BROKER", "1")
    policy = ExecutionPolicy()
    cmd = CommandRequest(verb=CommandVerb.HEALTH)
    assert policy.route(cmd) == "local"


def test_execution_policy_routes_local_without_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VDISPLAY_AGENT_URL", raising=False)
    monkeypatch.delenv("VDISPLAY_AGENT_BROKER", raising=False)
    policy = ExecutionPolicy()
    cmd = CommandRequest(verb=CommandVerb.HEALTH)
    assert policy.route(cmd) == "local"


def test_execute_health_local(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VDISPLAY_AGENT_URL", raising=False)
    result = execute(CommandRequest(verb=CommandVerb.HEALTH))
    assert result.ok is True
    assert result.data["status"] == "ok"
    assert result.meta["route"] == "local"


def test_execute_monitors_via_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_AGENT_URL", "http://127.0.0.1:8765")

    from vdisplay.application.commands import CommandResult

    class FakeClient:
        def request(self, cmd):
            return CommandResult.success(
                action=cmd.action,
                data={
                    "ok": True,
                    "monitor_count": 2,
                    "monitors": [{"name": "DP-1"}, {"name": "DP-2"}],
                    "resolved_display": ":0",
                },
            )

    monkeypatch.setattr("vdisplay.application.handlers.agent.agent_client_required", lambda: FakeClient())

    result = execute(CommandRequest(verb=CommandVerb.MONITORS))
    assert result.ok is True
    assert result.meta["route"] == "agent"
    assert result.data["monitor_count"] == 2
