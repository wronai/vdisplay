"""Fixtures for Playwright GUI tests against vdisplay-agent /web console."""

from __future__ import annotations

import json
import socket
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

TINY_PNG = b"\x89PNG\r\n\x1a\n" + (
    b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"
    b"\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc``\x00\x00\x00\x04\x00\x01"
    b"\x05\x27\x04\x1c\x00\x00\x00\x00IEND\xaeB`\x82"
)

OVERVIEW_FIXTURE: dict = {
    "monitors": {
        "monitor_count": 2,
        "monitors": [
            {
                "name": "DP-1",
                "width": 4096,
                "height": 2560,
                "x": 0,
                "y": 1304,
                "rotation": "normal",
            },
            {
                "name": "DP-2",
                "width": 4320,
                "height": 7680,
                "x": 4096,
                "y": 0,
                "rotation": "left",
            },
        ],
    },
    "screencast": {"active": True, "ready": True},
    "sampler": {"running": False},
    "tasks": {
        "tasks": [
            {"task_id": "task-sampler-1", "kind": "sampler", "status": "completed"},
        ]
    },
    "sessions": {"sessions": []},
    "windows": {
        "windows": [
            {
                "app_label": "firefox",
                "title": "Example Browser",
                "width": 1200,
                "height": 800,
                "x": 100,
                "y": 200,
            }
        ]
    },
    "capabilities": {"platform": "linux"},
}


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_port(port: int, *, timeout_s: float = 10.0) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise RuntimeError(f"web app did not listen on port {port}")


@pytest.fixture(scope="module")
def web_app_url(tmp_path_factory: pytest.TempPathFactory) -> str:
    """Start vdisplay-agent with mocked capture/overview for headless Playwright."""
    pytest.importorskip("uvicorn")
    tmp = tmp_path_factory.mktemp("web-e2e")
    png = tmp / "DP-1.png"
    png.write_bytes(TINY_PNG)

    replay_root = tmp / "sessions"
    session_dir = replay_root / "demo-session"
    (session_dir / "steps" / "0001").mkdir(parents=True)
    (session_dir / "session.json").write_text(
        json.dumps({"session_id": "demo-session", "updated_at": "2026-06-10T12:00:00Z"}),
        encoding="utf-8",
    )

    def fake_overview(_runtime, display=None):
        return OVERVIEW_FIXTURE

    def fake_frame(_runtime, monitor_name, **kwargs):
        return png

    def fake_sessions(root=None):
        return [
            {
                "session_id": "demo-session",
                "path": str(session_dir),
                "steps": 1,
                "updated_at": "2026-06-10T12:00:00Z",
                "source": "audit",
            }
        ]

    def fake_queue(session_id, root=None):
        return {
            "ok": True,
            "queued": True,
            "job_id": "test-job",
            "session_id": session_id,
            "session_path": str(session_dir),
            "steps": 1,
            "steps_replayable": 1,
            "message": "Replay started in background.",
        }

    def fake_screencast(*_args, **_kwargs):
        return {"active": True, "ready": True, "mock": True}

    def fake_sampler(*_args, **_kwargs):
        return {"running": True, "mock": True}

    patches = [
        patch("vdisplay_agent.services.web_console.build_overview", fake_overview),
        patch("vdisplay_agent.services.web_console.capture_monitor_frame", fake_frame),
        patch("vdisplay_agent.services.web_console.list_replay_sessions", fake_sessions),
        patch("vdisplay_agent.services.web_console.queue_replay", fake_queue),
        patch("vdisplay_agent.services.sessions.start_screencast", fake_screencast),
        patch("vdisplay_agent.services.sampler.start_sampler", fake_sampler),
        patch(
            "vdisplay_agent.services.web_console.click_monitor_pointer",
            lambda *_a, **_k: {
                "ok": True,
                "monitor": "DP-1",
                "global_x": 100,
                "global_y": 200,
                "method": "mock",
                "local_x": 10,
                "local_y": 10,
            },
        ),
    ]
    for item in patches:
        item.start()

    from vdisplay_agent.runtime import AgentRuntime
    from vdisplay_agent.server import create_app
    import uvicorn

    port = _free_port()
    app = create_app(AgentRuntime())
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    _wait_port(port)
    url = f"http://127.0.0.1:{port}"
    try:
        yield url
    finally:
        server.should_exit = True
        thread.join(timeout=5.0)
        for item in patches:
            item.stop()


@pytest.fixture(scope="module")
def playwright_browser():
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        yield browser
        browser.close()
