"""Event store and projections tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vdisplay.application.commands import CommandRequest, CommandResult, CommandVerb
from vdisplay.application.event_store import EventStore, event_store_enabled, read_events
from vdisplay.application.events import DomainEvent, command_completed, command_received
from vdisplay.application.executor import execute
from vdisplay.application.projections import build_backend_scores, refresh_projections


def test_event_store_disabled_without_session(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VDISPLAY_SESSION", raising=False)
    monkeypatch.delenv("VDISPLAY_SESSION_DIR", raising=False)
    monkeypatch.delenv("VDISPLAY_EVENT_STORE", raising=False)
    assert event_store_enabled() is False


def test_event_store_enabled_with_session(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_SESSION", "1")
    assert event_store_enabled() is True


def test_event_store_append_and_read(tmp_path: Path) -> None:
    store = EventStore(tmp_path)
    event = DomainEvent(
        event_id="evt-1",
        event_type="SessionStarted",
        occurred_at_ms=1,
        session_id="demo",
        body={"source": "cli"},
    )
    store.append(event)
    events = store.read_all()
    assert len(events) == 1
    assert events[0].event_type == "SessionStarted"
    assert (tmp_path / "index.jsonl").is_file()


def test_executor_writes_index_jsonl(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    session_dir = tmp_path / "events-session"
    monkeypatch.setenv("VDISPLAY_SESSION_DIR", str(session_dir))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "vdisplay.application.executor.execute_local",
        lambda cmd: {"ok": True, "monitor_count": 1, "monitors": []},
    )

    execute(
        CommandRequest(
            verb=CommandVerb.MONITORS,
            line="MONITORS",
            request_source="cli",
            session_id="demo",
        ),
        force_route="local",
    )

    events = read_events(session_dir)
    types = [event.event_type for event in events]
    assert "CommandReceived" in types
    assert "CommandCompleted" in types
    assert "SessionStarted" in types
    assert "StepRecorded" in types
    assert (session_dir / "projections" / "backend_scores.json").is_file()


def test_projections_backend_scores_from_control_events() -> None:
    events = [
        command_received(
            CommandRequest(verb=CommandVerb.CONTROL_SET_VALUE, request_id="r1", session_id="s1"),
            route="local",
        ),
        command_completed(
            CommandRequest(verb=CommandVerb.CONTROL_SET_VALUE, request_id="r1", session_id="s1"),
            CommandResult.success(
                action="control_set_value",
                data={},
                diagnostics={
                    "control": {
                        "routing": {
                            "selected_provider": "vision",
                            "application_profile": "pycharm@linux_wayland",
                        },
                        "verify": {"verified": True},
                    }
                },
            ),
            route="local",
            duration_ms=100,
        ),
    ]
    scores = build_backend_scores(events)
    assert "pycharm@linux_wayland" in scores
    assert scores["pycharm@linux_wayland"]["vision"]["success"] >= 1


def test_refresh_projections_writes_files(tmp_path: Path) -> None:
    store = EventStore(tmp_path)
    store.append(
        DomainEvent(
            event_id="1",
            event_type="SessionStarted",
            occurred_at_ms=1,
            session_id="demo",
            body={},
        )
    )
    refresh_projections(tmp_path)
    assert (tmp_path / "projections" / "control_state.json").is_file()
    payload = json.loads((tmp_path / "projections" / "control_state.json").read_text(encoding="utf-8"))
    assert "latest_by_request_id" in payload
