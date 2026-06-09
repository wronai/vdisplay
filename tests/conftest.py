"""Test isolation for vdisplay-agent broker env."""

from __future__ import annotations

import socket
import threading
import time
import urllib.error
import urllib.request

import pytest


@pytest.fixture(autouse=True)
def _isolate_agent_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VDISPLAY_AGENT_URL", raising=False)
    monkeypatch.delenv("VDISPLAY_AGENT_TOKEN", raising=False)
    monkeypatch.delenv("VDISPLAY_AGENT_BROKER", raising=False)
    monkeypatch.setenv("VDISPLAY_AGENT_AUTO", "0")
    from vdisplay.agent_config import reset_agent_probe_cache

    reset_agent_probe_cache()


@pytest.fixture(autouse=True)
def _reset_portal_screencast_state() -> None:
    from vdisplay.capture.portal_screencast import _set_active, stop_screencast_session

    stop_screencast_session()
    _set_active(None)
    yield
    stop_screencast_session()
    _set_active(None)


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


@pytest.fixture(scope="session")
def live_agent_url():
    pytest.importorskip("fastapi")
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
