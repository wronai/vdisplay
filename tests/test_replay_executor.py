"""Tests for .vdisplay session replay executor."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vdisplay.application.commands import CommandRequest, CommandResult, CommandVerb
from vdisplay.application.replay import (
    command_request_from_audit,
    queue_session_replay,
    replay_session,
)


def _write_step(session_dir: Path, step_id: str, verb: CommandVerb, **fields: object) -> None:
    step_dir = session_dir / "steps" / step_id
    step_dir.mkdir(parents=True)
    payload = {
        "verb": verb.value,
        "line": "",
        "request_source": "cli",
        "session_id": "test-session",
        "request_id": f"req-{step_id}",
        "display": None,
        "apps_only": False,
        "include_all": True,
        "match_class": None,
        "match_pid": None,
        "match_app": None,
        "match_title": None,
        "window_id": None,
        "min_width": 0,
        "min_height": 0,
        "output": None,
        "width": 1920,
        "height": 1080,
        "source": None,
        "target": None,
        "mode": "host",
        "all_monitors": False,
        "out_dir": None,
        "vd_display": ":99",
        "backend": "xvfb",
        "monitor": None,
        "local_only": False,
        "control_selector": None,
        "control_provider_ref": None,
        "control_name": None,
        "control_role": None,
        "control_app": None,
        "control_window_id": None,
        "control_window_title": None,
        "control_value": None,
        "control_verify": False,
        "control_screenshot_verify": False,
        "control_verify_label": None,
        "control_verify_selector": None,
        "control_backend": "auto",
        "control_index": 0,
        "control_max_depth": 8,
        "control_format": "flat",
        "control_environment": None,
        "control_text": None,
        "control_text_contains": None,
        "control_terminal_line": None,
        "control_terminal_col": None,
        "control_session_id": None,
        "terminal_session_id": None,
        "terminal_command": None,
        "terminal_rows": 24,
        "terminal_cols": 80,
        "terminal_title": None,
        "browser_session_id": None,
        "browser_url": None,
        "browser_headless": True,
        "browser_title": None,
        "browser_engine": None,
        "extra": {},
    }
    payload.update(fields)
    (step_dir / "request.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (step_dir / "result.json").write_text(json.dumps({"ok": True}), encoding="utf-8")


@pytest.fixture
def sample_session(tmp_path: Path) -> Path:
    session_dir = tmp_path / "demo-session"
    session_dir.mkdir()
    (session_dir / "session.json").write_text(
        json.dumps({"session_id": "demo-session", "updated_at": "2026-06-10T12:00:00Z"}),
        encoding="utf-8",
    )
    _write_step(session_dir, "0001", CommandVerb.HEALTH)
    _write_step(
        session_dir,
        "0002",
        CommandVerb.CONTROL_CLICK,
        control_name="Reload",
        control_role="button",
        control_app="firefox",
    )
    _write_step(session_dir, "0003", CommandVerb.CONTROL_FOCUS, control_name="Chat", control_app="jetbrains")
    return session_dir


def test_command_request_from_audit_roundtrip() -> None:
    from dataclasses import asdict

    original = CommandRequest(
        verb=CommandVerb.CONTROL_CLICK,
        control_name="Save",
        control_app="firefox",
        request_id="abc",
    )
    payload = asdict(original)
    payload["verb"] = original.verb.value
    rebuilt = command_request_from_audit(payload)
    assert rebuilt.verb == CommandVerb.CONTROL_CLICK
    assert rebuilt.control_name == "Save"
    assert rebuilt.request_id == "abc"


def test_replay_session_dry_run(sample_session: Path) -> None:
    report = replay_session(sample_session, dry_run=True, step_delay_s=0)
    assert report.session_id == "demo-session"
    assert report.steps_total == 3
    assert report.steps_replayable == 2
    assert report.steps_executed == 0
    assert len(report.plan) == 3


def test_replay_session_executes_control_steps(sample_session: Path) -> None:
    calls: list[CommandVerb] = []

    def fake_execute(cmd: CommandRequest) -> CommandResult:
        calls.append(cmd.verb)
        return CommandResult.success(action=cmd.action, data={"ok": True})

    report = replay_session(
        sample_session,
        dry_run=False,
        step_delay_s=0,
        stop_on_error=False,
        executor=fake_execute,
    )
    assert report.steps_executed == 2
    assert report.steps_ok == 2
    assert calls == [CommandVerb.CONTROL_CLICK, CommandVerb.CONTROL_FOCUS]


def test_queue_session_replay_returns_job(sample_session: Path) -> None:
    payload = queue_session_replay(sample_session, step_delay_s=0, executor=lambda _cmd: CommandResult.success(action="x", data={}))
    assert payload["queued"] is True
    assert payload["job_id"]
    assert payload["steps_replayable"] == 2
