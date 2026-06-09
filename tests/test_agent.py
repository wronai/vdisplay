from __future__ import annotations

import shutil

import pytest


def test_agent_health(agent_client) -> None:
    client, _runtime = agent_client
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["service"] == "vdisplay-agent"
    assert payload["data"]["broker"] == "vdisplay-agent"


def test_agent_capabilities(agent_client) -> None:
    client, _runtime = agent_client
    payload = client.get("/capabilities").json()
    assert payload["ok"] is True
    assert "capture_providers" in payload["data"]
    assert "virtual" in payload["data"]["session_modes"]


@pytest.mark.skipif(shutil.which("Xvfb") is None, reason="Xvfb not installed")
@pytest.mark.skipif(shutil.which("xwd") is None, reason="xwd not installed")
def test_agent_virtual_session_capture(agent_client, tmp_path) -> None:
    client, runtime = agent_client
    started = client.post("/session/virtual/start", json={"width": 64, "height": 64, "display": ":197"}).json()
    assert started["ok"] is True
    session_id = started["data"]["session_id"]
    out = tmp_path / "agent-virtual.png"
    captured = client.post(
        "/capture/frame",
        json={"session_id": session_id, "output": str(out)},
    ).json()
    assert captured["ok"] is True
    assert out.is_file()
    assert out.stat().st_size > 100
    stopped = client.post(f"/session/{session_id}/stop").json()
    assert stopped["ok"] is True
    assert session_id not in runtime.sessions
