"""Agent browser session lifecycle (PR-13)."""

from __future__ import annotations

import pytest

from fixtures.fake_browser import FakePage


@pytest.fixture
def agent_client_with_browser(monkeypatch: pytest.MonkeyPatch):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    from vdisplay.control.providers import browser_session as browser_mod
    from vdisplay.control.providers.browser_session import BrowserSessionRegistry
    from vdisplay_agent.runtime import AgentRuntime
    from vdisplay_agent.server import create_app

    registry = BrowserSessionRegistry()

    monkeypatch.setattr(browser_mod, "_DEFAULT_REGISTRY", registry)
    monkeypatch.setattr(
        browser_mod.BrowserSessionRegistry,
        "open",
        lambda self, url, *, session_id=None, headless=True, title=None, engine=None, page=None: self.open_mock(
            FakePage(),
            url=url,
            session_id=session_id or "browser-agent-1",
            title=title,
            engine=engine,
        ),
    )

    runtime = AgentRuntime()
    app = create_app(runtime)
    with TestClient(app) as client:
        yield client, runtime


def test_agent_browser_open_list_stop(agent_client_with_browser) -> None:
    client, runtime = agent_client_with_browser

    started = client.post(
        "/session/browser/open",
        json={"url": "https://example.test/app", "session_id": "browser-agent-1"},
    ).json()
    assert started["ok"] is True
    assert started["data"]["session_id"] == "browser-agent-1"
    assert started["data"]["mode"] == "browser"

    listed = client.get("/sessions").json()
    assert any(
        item["session_id"] == "browser-agent-1" and item["kind"] == "browser"
        for item in listed["data"]["sessions"]
    )

    stopped = client.post("/session/browser-agent-1/stop").json()
    assert stopped["ok"] is True
    assert "browser-agent-1" not in runtime.store.sessions
