from __future__ import annotations

import pytest

from vdisplay.agent_dispatch import dispatch_via_agent


def test_dispatch_monitors_via_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_AGENT_URL", "http://127.0.0.1:8765")

    class FakeClient:
        def outputs(self, *, display=None, include_all=True):
            return {
                "ok": True,
                "monitor_count": 1,
                "monitors": [{"name": "DP-1"}],
                "resolved_display": ":0",
            }

    monkeypatch.setattr("vdisplay.application.executor.agent_client_required", lambda: FakeClient())

    result = dispatch_via_agent({"verb": "MONITORS"}, line="MONITORS")
    assert result.ok is True
    assert result.action == "monitors"
    assert result.data["monitor_count"] == 1


def test_dsl_bus_uses_executor_when_agent_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_AGENT_URL", "http://127.0.0.1:8765")

    from vdisplay.application.commands import CommandResult

    def fake_execute(request, **kwargs):
        return CommandResult.success(
            action=request.action,
            data={"via": "agent"},
            command=request.line,
            meta={"route": "agent"},
        )

    monkeypatch.setattr("vdisplay.application.executor.execute", fake_execute)

    from dsl2vdisplay import dispatch

    result = dispatch("HEALTH")
    assert result.ok is True
    assert result.data.get("via") == "agent"
