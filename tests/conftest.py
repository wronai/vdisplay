"""Test isolation for vdisplay-agent broker env."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolate_agent_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VDISPLAY_AGENT_URL", raising=False)
    monkeypatch.delenv("VDISPLAY_AGENT_TOKEN", raising=False)
    monkeypatch.delenv("VDISPLAY_AGENT_BROKER", raising=False)


@pytest.fixture
def agent_client():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    from vdisplay_agent.runtime import AgentRuntime
    from vdisplay_agent.server import create_app

    runtime = AgentRuntime()
    app = create_app(runtime)
    with TestClient(app) as client:
        yield client, runtime
