from __future__ import annotations

import pytest


def test_agent_control_diagnostics(agent_client, monkeypatch: pytest.MonkeyPatch) -> None:
    client, _runtime = agent_client
    monkeypatch.setattr(
        "vdisplay.control.scoring._atspi_ready",
        lambda: (True, "AT-SPI2 bus active"),
    )
    payload = client.get("/diagnostics/control").json()
    assert payload["ok"] is True
    assert "control" in payload["data"]
    assert "routing" in payload["data"]
    assert payload["data"]["routing"]["selected_provider"]
    assert "extensions" in payload["data"]
    assert len(payload["data"]["extensions"]["providers"]) >= 7


def test_agent_controls_list(agent_client, monkeypatch: pytest.MonkeyPatch) -> None:
    client, _runtime = agent_client
    monkeypatch.setattr(
        "vdisplay.application.services.control.controls_list",
        lambda **kwargs: {
            "ok": True,
            "backend": "atspi",
            "count": 2,
            "nodes": {},
            "root_ids": [],
        },
    )
    payload = client.post("/controls/list", json={"backend": "atspi", "max_depth": 2}).json()
    assert payload["ok"] is True
    assert payload["data"]["count"] == 2
