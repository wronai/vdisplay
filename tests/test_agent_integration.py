from __future__ import annotations

import socket
import threading
import time
import urllib.error
import urllib.request

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


def _wait_for_url(url: str, *, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=0.3) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.05)
    raise RuntimeError(f"service not ready: {url}")


@pytest.fixture
def live_agent_url():
    import uvicorn
    from vdisplay_agent.runtime import AgentRuntime
    from vdisplay_agent.server import create_app

    runtime = AgentRuntime()
    app = create_app(runtime)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    base = f"http://127.0.0.1:{port}"
    _wait_for_url(f"{base}/health")
    yield base

    server.should_exit = True
    thread.join(timeout=5)


def test_agent_client_round_trip_monitors(live_agent_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_AGENT_URL", live_agent_url)

    from vdisplay.client import AgentClient

    payload = AgentClient(live_agent_url).outputs()
    assert payload.get("monitor_count", 0) >= 0
    assert "monitors" in payload


def test_dsl_dispatch_round_trip(live_agent_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_AGENT_URL", live_agent_url)

    from dsl2vdisplay import dispatch

    health = dispatch("HEALTH")
    assert health.ok is True
    assert health.action == "health"

    monitors = dispatch("MONITORS")
    assert monitors.ok is True
    assert monitors.action == "monitors"
    assert "monitor_count" in monitors.data


def test_rest2vdisplay_round_trip(live_agent_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("rest2vdisplay")
    monkeypatch.setenv("VDISPLAY_AGENT_URL", live_agent_url)

    from rest2vdisplay.app import create_app

    client = TestClient(create_app(agent_url=live_agent_url))
    health = client.get("/health").json()
    assert health["status"] == "ok"
    assert health["broker"] == live_agent_url

    monitors = client.post("/v1/dsl", json={"verb": "MONITORS"}).json()
    assert monitors["ok"] is True
    assert monitors["action"] == "monitors"


@pytest.mark.skipif(
    __import__("shutil").which("Xvfb") is None or __import__("shutil").which("xwd") is None,
    reason="Xvfb/xwd required",
)
def test_virtual_screenshot_round_trip(
    live_agent_url: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("VDISPLAY_AGENT_URL", live_agent_url)

    from dsl2vdisplay import dispatch

    out = tmp_path / "agent-roundtrip.png"
    result = dispatch(f"SCREENSHOT OUT {out} DISPLAY :196 WIDTH 64 HEIGHT 64")
    assert result.ok is True, result.error
    assert out.is_file()
    assert out.stat().st_size > 100
