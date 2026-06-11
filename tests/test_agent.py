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


def test_agent_capture_recovers_missing_screencast(
    agent_client,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    client, runtime = agent_client
    calls = {"n": 0}

    def fake_capture_host_to_file(path, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise __import__("vdisplay.exceptions", fromlist=["VDisplayError"]).VDisplayError(
                "portal-screencast: no active session"
            )
        out = __import__("pathlib").Path(path)
        out.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 200)
        return {"path": str(out), "method": "portal-screencast", "bytes": out.stat().st_size}

    monkeypatch.setattr("vdisplay_agent.services.capture.capture_host_to_file", fake_capture_host_to_file)
    monkeypatch.setattr(
        "vdisplay_agent.services.capture.try_recover_screencast",
        lambda store, **kwargs: setattr(store, "screencast", object()) or True,
    )

    out = tmp_path / "host.png"
    payload = client.post(
        "/capture/frame",
        json={"output": str(out), "source": "DP-1", "monitor": 1},
    ).json()
    assert payload["ok"] is True
    assert calls["n"] == 2
    assert out.is_file()


def test_agent_capture_reraises_non_recoverable_screencast_error(
    agent_client,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    client, runtime = agent_client
    from vdisplay.capture.portal_screencast import PortalScreenCastSession

    session = PortalScreenCastSession()
    session.active = True
    session.session_path = "/org/test/session"
    session.node_ids = [1]
    runtime.store.screencast = session

    def fake_capture_host_to_file(path, **kwargs):
        raise __import__("vdisplay.exceptions", fromlist=["VDisplayError"]).VDisplayError(
            "portal-screencast capture failed: keeper socket missing"
        )

    monkeypatch.setattr("vdisplay_agent.services.capture.capture_host_to_file", fake_capture_host_to_file)

    out = tmp_path / "host.png"
    response = client.post(
        "/capture/frame",
        json={"output": str(out), "source": "DP-1", "monitor": 1},
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["ok"] is False
    assert "keeper socket missing" in payload["error"]["message"]
    assert not out.is_file()


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
