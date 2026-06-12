from __future__ import annotations

import base64

import pytest

_PNG = b"\x89PNG\r\n\x1a\n" + b"w" * 128


def test_web_console_page(agent_client) -> None:
    client, _runtime = agent_client
    res = client.get("/web")
    assert res.status_code == 200
    assert "vdisplay console" in res.text


def test_web_overview(agent_client, monkeypatch: pytest.MonkeyPatch) -> None:
    client, runtime = agent_client
    monkeypatch.setattr(
        "vdisplay_agent.services.web_console.build_overview",
        lambda _runtime, display=None: {
            "monitors": {"monitors": [{"name": "DP-1", "width": 1920, "height": 1080, "x": 0, "y": 0}]},
            "screencast": {"active": False, "ready": False},
            "sampler": {"running": False},
            "tasks": {"tasks": []},
            "sessions": {"sessions": []},
            "windows": {"windows": []},
            "capabilities": {},
        },
    )
    payload = client.get("/api/web/overview").json()
    assert payload["ok"] is True
    assert payload["data"]["monitors"]["monitors"][0]["name"] == "DP-1"


def test_web_frame_endpoint(agent_client, monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    client, _runtime = agent_client
    png = tmp_path / "DP-1.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 64)
    monkeypatch.setattr(
        "vdisplay_agent.services.web_console.capture_monitor_frame",
        lambda *_a, **_k: png,
    )
    res = client.get("/api/web/frame/DP-1")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("image/png")


def test_web_frame_endpoint_rejects_active_screencast_without_keeper(agent_client) -> None:
    client, runtime = agent_client
    from vdisplay.capture.portal_screencast import PortalScreenCastSession

    session = PortalScreenCastSession()
    session.active = True
    session.session_path = "/org/test/session"
    session.node_ids = [80, 81]
    runtime.store.screencast = session

    res = client.get("/api/web/frame/DP-1")
    assert res.status_code == 503
    assert "frame keeper is not running" in res.text
    assert "screencast start --force" in res.text


def test_web_frame_endpoint_uses_browser_bridge_before_screencast(agent_client) -> None:
    client, _runtime = agent_client
    registered = client.post(
        "/session/browser-bridge/register",
        json={"client": "test-electron", "sources": ["DP-1"], "ttl_s": 10},
    ).json()
    bridge_id = registered["data"]["bridge_id"]
    ingested = client.post(
        "/capture/ingest",
        json={
            "bridge_id": bridge_id,
            "source": "DP-1",
            "png_base64": base64.b64encode(_PNG).decode("ascii"),
        },
    ).json()
    assert ingested["ok"] is True

    res = client.get("/api/web/frame/DP-1")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("image/png")
    assert res.content == _PNG


def test_web_replay_sessions(agent_client, monkeypatch: pytest.MonkeyPatch) -> None:
    client, _runtime = agent_client
    monkeypatch.setattr(
        "vdisplay_agent.services.web_console.list_replay_sessions",
        lambda root=None: [{"session_id": "demo", "steps": 3, "path": "/tmp/demo"}],
    )
    payload = client.get("/api/web/replay/sessions").json()
    assert payload["ok"] is True
    assert payload["data"]["sessions"][0]["session_id"] == "demo"


def test_web_replay_start(agent_client, monkeypatch: pytest.MonkeyPatch) -> None:
    client, _runtime = agent_client
    monkeypatch.setattr(
        "vdisplay_agent.services.web_console.queue_replay",
        lambda session_id, root=None: {"ok": True, "queued": True, "session_id": session_id},
    )
    payload = client.post("/api/web/replay/start", json={"session_id": "demo"}).json()
    assert payload["ok"] is True
    assert payload["data"]["queued"] is True


def test_web_pointer_click(agent_client, monkeypatch: pytest.MonkeyPatch) -> None:
    client, _runtime = agent_client
    monkeypatch.setattr(
        "vdisplay_agent.services.web_console.click_monitor_pointer",
        lambda *_a, **_k: {
            "ok": True,
            "monitor": "DP-1",
            "global_x": 100,
            "global_y": 200,
            "method": "mock",
        },
    )
    payload = client.post(
        "/api/web/pointer/click",
        json={"monitor_name": "DP-1", "x": 10, "y": 20},
    ).json()
    assert payload["ok"] is True
    assert payload["data"]["global_x"] == 100
