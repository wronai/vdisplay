from __future__ import annotations

from vdisplay.control.providers.terminal_session import default_registry
from vdisplay_agent.runtime import AgentRuntime
from vdisplay_agent.services import control as agent_control


def test_agent_open_terminal_session_and_find() -> None:
    default_registry().close_all()
    runtime = AgentRuntime()
    opened = runtime.start_terminal(session_id="demo", lines=["READY", "Name:"])
    assert opened["ok"] is True
    assert opened["session_id"] == "demo"

    found = agent_control.find_controls(
        {
            "backend": "terminal",
            "session_id": "demo",
            "text": "READY",
        }
    )
    assert found["ok"] is True
    assert found["count"] >= 1

    runtime.stop_session("demo")
    default_registry().close_all()
