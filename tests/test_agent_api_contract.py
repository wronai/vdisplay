from __future__ import annotations

import pytest

pytest.importorskip("vdisplay_agent")
from vdisplay_agent.envelope import flatten_envelope, success


def test_agent_health_envelope(agent_client) -> None:
    client, _runtime = agent_client
    payload = client.get("/health").json()
    assert payload["ok"] is True
    assert payload["action"] == "health"
    assert payload["data"]["service"] == "vdisplay-agent"
    assert payload["meta"]["broker"] == "vdisplay-agent"


def test_agent_capabilities_envelope(agent_client) -> None:
    client, _runtime = agent_client
    payload = client.get("/capabilities").json()
    assert payload["ok"] is True
    assert payload["action"] == "capabilities"
    assert "capture_providers" in payload["data"]
    assert "virtual" in payload["data"]["session_modes"]


def test_flatten_envelope_for_sdk() -> None:
    envelope = success("outputs", {"monitor_count": 2, "monitors": []})
    flat = flatten_envelope(envelope)
    assert flat["ok"] is True
    assert flat["monitor_count"] == 2
