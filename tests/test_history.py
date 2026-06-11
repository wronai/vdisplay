from __future__ import annotations

import json
from pathlib import Path

import pytest

from vdisplay.application.history.analyze import analyze_history, collect_events
from vdisplay.application.history.loader import (
    discover_session_dirs,
    load_history_index,
    load_run_detail,
    load_task_record,
)
from vdisplay.application.session_recorder import discover_session_dirs as legacy_discover


def _write_session(session_dir: Path, *, session_id: str, steps: int = 1) -> None:
    session_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "session_id": session_id,
        "started_at": "2026-06-11T10:00:00Z",
        "updated_at": "2026-06-11T10:01:00Z",
        "source": "cli",
        "route_default": "local",
        "host": "test",
        "cwd": "/tmp",
        "pid": 1,
        "env": {},
        "steps": [
            {
                "index": 1,
                "step_id": "0001",
                "request_id": "req-1",
                "timestamp": "2026-06-11T10:00:01Z",
                "duration_ms": 10,
                "source": "cli",
                "route": "local",
                "verb": "CONTROL_CLICK",
                "action": "control click",
                "command_line": "vdisplay control click",
                "ok": True,
                "request_path": "steps/0001/request.json",
                "result_path": "steps/0001/result.json",
                "artifacts": [],
                "diagnostics": {"routing": {"selected_provider": "vision"}},
            }
        ],
        "summary": {"total_steps": steps, "ok_steps": steps, "failed_steps": 0, "backends_used": ["vision"]},
        "maps": [],
    }
    (session_dir / "session.json").write_text(json.dumps(payload), encoding="utf-8")
    (session_dir / "index.jsonl").write_text(
        json.dumps(
            {
                "event_id": "e1",
                "event_type": "StepRecorded",
                "occurred_at_ms": 1000,
                "session_id": session_id,
                "request_id": "req-1",
                "aggregate": "audit_session",
                "body": {"backend": "vision"},
            }
        )
        + "\n",
        encoding="utf-8",
    )


def _write_run(root: Path, run_id: str, *, task_ok: bool = True) -> None:
    run_dir = root / "runs" / run_id
    (run_dir / "tasks").mkdir(parents=True)
    manifest = {
        "run_id": run_id,
        "started_at": "2026-06-11T10:00:00Z",
        "project": str(root.parent),
        "config_path": None,
        "config": {},
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    task = {
        "task_id": "task-a",
        "recorded_at": "2026-06-11T10:00:05Z",
        "payload": {
            "ok": task_ok,
            "task": {"id": "task-a", "command": "vdisplay control find", "monitor": "DP-1"},
            "method": "vdisplay-cli",
            "feedback": {
                "observe_path": str(root / "observe/task-a.png"),
                "vql_path": str(root / "observe/task-a.png.vql.json"),
                "decision_data": {"vql_targets": [{"id": "btn-1"}]},
            },
            "exit_code": 0 if task_ok else 1,
        },
        "observe_artifacts": [],
    }
    (run_dir / "tasks" / "task-a.json").write_text(json.dumps(task), encoding="utf-8")
    _write_session(run_dir / "session", session_id=f"session-{run_id}")


@pytest.fixture
def metadata_root(tmp_path: Path) -> Path:
    root = tmp_path / ".vdisplay"
    root.mkdir()
    _write_session(root / "2026-06-11T10-00-00Z__local__cli", session_id="flat-session")
    _write_run(root, "2026-06-11T10-05-00Z", task_ok=True)
    (root / "latest-run.txt").write_text("2026-06-11T10-05-00Z\n", encoding="utf-8")
    (root / "broker.jsonl").write_text(
        '{"ts":"2026-06-11T10:00:00Z","action":"screencast_start","ok":false,"error":"denied"}\n',
        encoding="utf-8",
    )
    observe = root / "observe"
    observe.mkdir()
    (observe / "task-a.png").write_bytes(b"png")
    (observe / "task-a.png.vql.json").write_text("{}", encoding="utf-8")
    return root


def test_discover_session_dirs_includes_flat_and_run_sessions(metadata_root: Path) -> None:
    sessions = discover_session_dirs(root=metadata_root)
    assert len(sessions) == 2
    locations = {path.name for path in sessions}
    assert "session" in locations
    assert any(path.name.startswith("2026-06-11") for path in sessions)


def test_legacy_discover_delegates_to_history_loader(metadata_root: Path) -> None:
    assert len(legacy_discover(root=metadata_root)) == 2


def test_load_history_index(metadata_root: Path) -> None:
    index = load_history_index(metadata_root)
    assert index.latest_run_id == "2026-06-11T10-05-00Z"
    assert len(index.runs) == 1
    assert len(index.sessions) == 2
    assert len(index.tasks) == 1
    assert index.tasks[0].vql_targets == 1
    assert index.observe_png_count == 1
    assert len(index.broker_events) == 1


def test_load_run_detail(metadata_root: Path) -> None:
    detail = load_run_detail("2026-06-11T10-05-00Z", root=metadata_root)
    assert detail is not None
    assert detail["run"]["tasks_ok"] == 1
    assert detail["session"]["location"] == "run"


def test_analyze_history(metadata_root: Path) -> None:
    report = analyze_history(metadata_root)
    assert report.summary["runs"] == 1
    assert report.summary["sessions"] == 2
    assert report.summary["tasks"] == 1
    assert report.summary["broker_errors"] == 1
    assert "StepRecorded" in report.event_histogram
    assert report.observe_artifacts["png"] == 1


def test_collect_events_by_run(metadata_root: Path) -> None:
    events = collect_events(root=metadata_root, run_id="2026-06-11T10-05-00Z")
    assert len(events) == 1
    assert events[0]["event_type"] == "StepRecorded"
    assert events[0]["run_id"] == "2026-06-11T10-05-00Z"


def test_load_task_record(metadata_root: Path) -> None:
    task_path = metadata_root / "runs" / "2026-06-11T10-05-00Z" / "tasks" / "task-a.json"
    record = load_task_record(task_path, run_id="2026-06-11T10-05-00Z")
    assert record is not None
    assert record.ok is True
    assert record.vql_targets == 1
