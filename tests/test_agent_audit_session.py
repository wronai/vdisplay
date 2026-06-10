"""Agent broker audit session propagation (PR-F / PR-G)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vdisplay.application.commands import CommandRequest, CommandVerb
from vdisplay.application.executor import execute
from vdisplay.application.session_context import (
    HEADER_REQUEST_ID,
    HEADER_REQUEST_SOURCE,
    HEADER_SESSION_DIR,
    HEADER_SESSION_ID,
    audit_headers_for_command,
    bind_audit_command,
)
from vdisplay.client import AgentClient


def test_audit_headers_for_command_includes_session_dir(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    session_dir = tmp_path / "shared-audit"
    monkeypatch.setenv("VDISPLAY_SESSION_DIR", str(session_dir))
    cmd = CommandRequest(
        verb=CommandVerb.CONTROL_CLICK,
        session_id="demo-run",
        request_id="req-123",
        request_source="cli",
    )
    headers = audit_headers_for_command(cmd)
    assert headers[HEADER_SESSION_ID] == "demo-run"
    assert headers[HEADER_REQUEST_ID] == "req-123"
    assert headers[HEADER_REQUEST_SOURCE] == "cli"
    assert headers[HEADER_SESSION_DIR] == str(session_dir.resolve())


def test_client_sends_audit_headers(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    captured: dict[str, str] = {}

    class FakeResponse:
        def read(self) -> bytes:
            return json.dumps({"ok": True, "action": "health", "data": {"status": "ok"}}).encode()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_urlopen(request, **kwargs):
        captured.update({key.lower(): value for key, value in request.header_items()})
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    monkeypatch.setenv("VDISPLAY_SESSION_DIR", str(tmp_path / "audit"))

    cmd = CommandRequest(
        verb=CommandVerb.HEALTH,
        session_id="broker-audit",
        request_id="req-abc",
        request_source="cli",
    )
    client = AgentClient("http://127.0.0.1:8765")
    with bind_audit_command(cmd):
        client.health()

    assert captured[HEADER_SESSION_ID.lower()] == "broker-audit"
    assert captured[HEADER_REQUEST_ID.lower()] == "req-abc"
    assert captured[HEADER_REQUEST_SOURCE.lower()] == "cli"
    assert captured[HEADER_SESSION_DIR.lower()] == str((tmp_path / "audit").resolve())


def test_broker_records_control_step_with_audit_headers(
    agent_client,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    client, _runtime = agent_client
    session_dir = tmp_path / "broker-session"
    monkeypatch.setattr(
        "vdisplay.application.services.control.controls_list",
        lambda **kwargs: {
            "ok": True,
            "backend": "atspi",
            "count": 1,
            "nodes": {},
            "root_ids": [],
        },
    )

    response = client.post(
        "/controls/list",
        json={"backend": "atspi", "max_depth": 2},
        headers={
            HEADER_SESSION_DIR: str(session_dir),
            HEADER_REQUEST_ID: "broker-req-1",
            HEADER_REQUEST_SOURCE: "cli",
            HEADER_SESSION_ID: "wayland-run",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["meta"]["session_dir"] == str(session_dir)
    assert (session_dir / "session.json").is_file()
    assert (session_dir / "steps" / "0001" / "request.json").is_file()
    session = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    assert session["summary"]["total_steps"] == 1
    assert session["steps"][0]["route"] == "local"


def test_broker_records_browser_open_with_audit_headers(
    agent_client,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    client, _runtime = agent_client
    session_dir = tmp_path / "browser-audit"
    monkeypatch.setattr(
        "vdisplay.application.services.session.browser_open",
        lambda **kwargs: {
            "ok": True,
            "session_id": kwargs.get("session_id") or "web-ff",
            "mode": "browser",
            "url": kwargs.get("url"),
            "engine": kwargs.get("engine") or "firefox",
            "headless": bool(kwargs.get("headless", True)),
        },
    )

    response = client.post(
        "/session/browser/open",
        json={
            "url": "https://example.com",
            "session_id": "web-ff",
            "headless": True,
            "engine": "firefox",
        },
        headers={
            HEADER_SESSION_DIR: str(session_dir),
            HEADER_REQUEST_ID: "browser-req-1",
            HEADER_REQUEST_SOURCE: "cli",
            HEADER_SESSION_ID: "dsl-run",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["meta"]["session_dir"] == str(session_dir)
    assert (session_dir / "steps" / "0001" / "request.json").is_file()
    session = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    assert session["steps"][0]["verb"] == "BROWSER_OPEN"


def test_broker_records_virtual_start_with_audit_headers(
    agent_client,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    client, _runtime = agent_client
    session_dir = tmp_path / "virtual-audit"
    monkeypatch.setattr(
        "vdisplay_agent.services.sessions.start_virtual",
        lambda store, **kwargs: {
            "ok": True,
            "session_id": "virt-1",
            "mode": "virtual",
            "display": kwargs.get("display"),
        },
    )

    response = client.post(
        "/session/virtual/start",
        json={"width": 1280, "height": 720, "display": ":99"},
        headers={
            HEADER_SESSION_DIR: str(session_dir),
            HEADER_REQUEST_ID: "virt-req-1",
            HEADER_REQUEST_SOURCE: "cli",
            HEADER_SESSION_ID: "virt-run",
        },
    )

    assert response.status_code == 200
    session = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    assert session["steps"][0]["verb"] == "VIRTUAL_START"


def test_broker_records_window_adopt_with_audit_headers(
    agent_client,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    client, _runtime = agent_client
    session_dir = tmp_path / "adopt-audit"
    monkeypatch.setattr(
        "vdisplay.application.services.session.relay_adopt",
        lambda **kwargs: {"ok": True, "window_id": kwargs.get("window_id") or "win-1"},
    )

    response = client.post(
        "/window/adopt",
        json={"window_id": "0xabc", "target": "offscreen"},
        headers={
            HEADER_SESSION_DIR: str(session_dir),
            HEADER_REQUEST_ID: "adopt-req-1",
            HEADER_REQUEST_SOURCE: "cli",
            HEADER_SESSION_ID: "adopt-run",
        },
    )

    assert response.status_code == 200
    session = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    assert session["steps"][0]["verb"] == "ADOPT"


def test_executor_skips_client_record_when_agent_audit_delegated(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    session_dir = tmp_path / "delegated"
    monkeypatch.setenv("VDISPLAY_SESSION_DIR", str(session_dir))
    monkeypatch.setenv("VDISPLAY_AGENT_AUDIT_DELEGATE", "1")
    monkeypatch.chdir(tmp_path)

    recorded = {"called": False}

    def fake_record(*args, **kwargs):
        recorded["called"] = True
        return session_dir

    monkeypatch.setattr("vdisplay.application.executor.record_execution", fake_record)
    monkeypatch.setattr(
        "vdisplay.application.executor.execute_agent",
        lambda cmd: {"ok": True, "count": 0},
    )

    result = execute(
        CommandRequest(verb=CommandVerb.CONTROLS_LIST, request_source="cli"),
        force_route="agent",
    )

    assert result.ok is True
    assert recorded["called"] is False
    assert result.meta.get("audit_delegated") == "broker"
    assert result.meta.get("session_dir") == str(session_dir.resolve())
