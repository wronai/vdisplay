from __future__ import annotations

import base64
import shutil

import pytest

_PNG = b"\x89PNG\r\n\x1a\n" + b"x" * 200


def test_agent_health(agent_client) -> None:
    client, _runtime = agent_client
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["service"] == "vdisplay-agent"
    assert payload["data"]["broker"] == "vdisplay-agent"
    assert payload["data"]["executable"]
    assert payload["data"]["package_file"].endswith("vdisplay_agent/routes/health.py")


def test_agent_capabilities(agent_client) -> None:
    client, _runtime = agent_client
    payload = client.get("/capabilities").json()
    assert payload["ok"] is True
    assert "capture_providers" in payload["data"]
    assert "virtual" in payload["data"]["session_modes"]


def test_agent_adopt_rejects_wayland_screencast_without_keeper(
    agent_client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _runtime = agent_client
    monkeypatch.setattr(
        "vdisplay_agent.services.sessions._is_wayland_host_session",
        lambda: True,
    )
    monkeypatch.setattr(
        "vdisplay_agent.services.sessions._keeper_capture_ready_for_session",
        lambda _session: False,
    )

    response = client.post(
        "/session/screencast/adopt",
        json={
            "session_path": "/org/test/session",
            "active": True,
            "ready": True,
            "node_ids": [1],
            "streams": [
                {
                    "node_id": 1,
                    "properties": {
                        "id": "0",
                        "source_type": 1,
                        "position": [0, 0],
                        "size": [2048, 1280],
                    },
                }
            ],
        },
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["ok"] is False
    assert "frame keeper is not running" in payload["error"]["message"]
    status = client.get("/session/screencast/status").json()
    assert status["data"]["active"] is False


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
    monkeypatch.setenv("VDISPLAY_ALLOW_DIRECT_SCREENCAST_CAPTURE", "1")

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


def test_agent_capture_failure_degrades_screencast_capture_ready(
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
    monkeypatch.setenv("VDISPLAY_ALLOW_DIRECT_SCREENCAST_CAPTURE", "1")
    monkeypatch.setattr(
        "vdisplay_agent.services.sessions._keeper_capture_ready_for_session",
        lambda _session: True,
    )

    def fake_capture_host_to_file(path, **kwargs):
        raise __import__("vdisplay.exceptions", fromlist=["VDisplayError"]).VDisplayError(
            "pipewire timed out"
        )

    monkeypatch.setattr("vdisplay_agent.services.capture.capture_host_to_file", fake_capture_host_to_file)

    out = tmp_path / "host.png"
    response = client.post(
        "/capture/frame",
        json={"output": str(out), "source": "DP-1", "monitor": 1},
    )
    assert response.status_code == 400
    payload = client.get("/session/screencast/status").json()
    assert payload["ok"] is True
    assert payload["data"]["capture_socket_ready"] is True
    assert payload["data"]["capture_ready"] is False
    assert "pipewire timed out" in payload["data"]["capture_last_error"]
    assert "last frame capture failed" in payload["data"]["capture_hint"]


def test_agent_capture_reports_stream_index_error_as_invalid_request(
    agent_client,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    client, runtime = agent_client
    runtime.store.screencast = object()

    def fake_capture_host_to_file(path, **kwargs):
        raise IndexError("list index out of range")

    monkeypatch.setattr("vdisplay_agent.services.capture.capture_host_to_file", fake_capture_host_to_file)

    out = tmp_path / "host.png"
    response = client.post(
        "/capture/frame",
        json={"output": str(out), "source": "HDMI-1", "monitor": 1},
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["ok"] is False
    assert payload["error"]["code"] == "invalid_request"
    assert "screencast stream mapping failed" in payload["error"]["message"]
    assert "screencast probe --via-agent" in payload["error"]["message"]
    assert not out.is_file()


def test_agent_capture_rejects_wayland_screencast_without_keeper(
    agent_client,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    client, runtime = agent_client
    from vdisplay.capture.portal_screencast import PortalScreenCastSession

    session = PortalScreenCastSession()
    session.active = True
    session.session_path = "/org/test/session"
    session.node_ids = [80, 81]
    runtime.store.screencast = session
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.delenv("VDISPLAY_ALLOW_DIRECT_SCREENCAST_CAPTURE", raising=False)
    monkeypatch.delenv("VDISPLAY_ELECTRON_SHARE_URL", raising=False)
    monkeypatch.setenv("VDISPLAY_ELECTRON_SHARE", "0")
    monkeypatch.setattr(
        "vdisplay.capture.linux_xwd._is_wayland_session",
        lambda: True,
    )
    monkeypatch.setattr(
        "vdisplay.capture.screencast_keeper.session_uses_keeper",
        lambda _session: False,
    )
    monkeypatch.setattr(
        "vdisplay.capture.screencast_keeper.keeper_capture_ready",
        lambda *_args, **_kwargs: False,
    )

    def fail_capture_host_to_file(*_args, **_kwargs):
        raise AssertionError("capture_host_to_file should not run without keeper")

    monkeypatch.setattr("vdisplay_agent.services.capture.capture_host_to_file", fail_capture_host_to_file)

    out = tmp_path / "host.png"
    response = client.post(
        "/capture/frame",
        json={"output": str(out), "source": "HDMI-1", "monitor": 1},
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["ok"] is False
    assert "frame keeper is not running" in payload["error"]["message"]
    assert "screencast start --force" in payload["error"]["message"]
    assert not out.is_file()


def test_agent_browser_bridge_ingest_drives_capture(agent_client, tmp_path) -> None:
    client, _runtime = agent_client
    registered = client.post(
        "/session/browser-bridge/register",
        json={"client": "test-electron", "version": "0", "sources": ["HDMI-1"], "ttl_s": 10},
    ).json()
    assert registered["ok"] is True
    bridge_id = registered["data"]["bridge_id"]

    heartbeat = client.post(
        "/session/browser-bridge/heartbeat",
        json={"bridge_id": bridge_id, "sharing": True, "sources": ["HDMI-1"], "fps": 2},
    ).json()
    assert heartbeat["ok"] is True

    ingested = client.post(
        "/capture/ingest",
        json={
            "bridge_id": bridge_id,
            "source": "HDMI-1",
            "seq": 1,
            "mime": "image/png",
            "png_base64": base64.b64encode(_PNG).decode("ascii"),
            "width": 10,
            "height": 10,
            "display_id": "1",
            "display_label": "HDMI display",
            "source_id": "screen:1",
            "source_name": "Entire screen",
            "display_bounds": {"x": 0, "y": 0, "width": 2048, "height": 1280},
        },
    ).json()
    assert ingested["ok"] is True
    assert ingested["data"]["capture_ready"] is True

    status = client.get("/session/browser-bridge/status").json()
    assert status["data"]["capture_ready"] is True
    assert status["data"]["monitors"]["HDMI-1"]["display_id"] == "1"
    assert status["data"]["monitors"]["HDMI-1"]["display_bounds"]["width"] == 2048
    screencast = client.get("/session/screencast/status").json()
    assert screencast["data"]["capture_ready"] is True
    assert screencast["data"]["keeper_mode"] == "browser_bridge"

    out = tmp_path / "bridge.png"
    captured = client.post(
        "/capture/frame",
        json={"output": str(out), "source": "HDMI-1"},
    ).json()
    assert captured["ok"] is True
    data = captured.get("data") or captured
    assert data["method"] == "browser-bridge"
    assert data["keeper_mode"] == "browser_bridge"
    assert data["source"] == "HDMI-1"
    assert data["display_label"] == "HDMI display"
    assert data["source_name"] == "Entire screen"
    assert data["png_base64"]
    assert out.read_bytes() == _PNG


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
