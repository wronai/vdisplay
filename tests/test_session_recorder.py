"""Session recorder hooked from application.executor."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vdisplay.application.commands import ArtifactRef, CommandRequest, CommandVerb
from vdisplay.application.executor import execute
from vdisplay.application.session_recorder import (
    collect_artifacts,
    render_readme,
    session_recording_enabled,
)


def test_session_recording_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VDISPLAY_SESSION", raising=False)
    monkeypatch.delenv("VDISPLAY_SESSION_DIR", raising=False)
    assert session_recording_enabled() is False


def test_executor_writes_session_dir(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    session_dir = tmp_path / "audit-session"
    monkeypatch.setenv("VDISPLAY_SESSION_DIR", str(session_dir))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "vdisplay.application.executor.execute_local",
        lambda cmd: {"ok": True, "monitor_count": 1, "monitors": []},
    )

    result = execute(
        CommandRequest(
            verb=CommandVerb.MONITORS,
            line="MONITORS",
            request_source="cli",
        ),
        force_route="local",
    )

    assert result.ok is True
    assert result.meta.get("session_dir") == str(session_dir)
    assert (session_dir / "README.md").is_file()
    assert (session_dir / "session.json").is_file()
    assert (session_dir / "steps" / "0001" / "request.json").is_file()
    assert (session_dir / "steps" / "0001" / "result.json").is_file()
    assert (session_dir / "steps" / "0001" / "diagnostics.json").is_file()

    readme = (session_dir / "README.md").read_text(encoding="utf-8")
    assert "Step 0001 — MONITORS" in readme
    session = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    assert session["summary"]["total_steps"] == 1


def test_collect_artifacts_from_explicit_and_data(tmp_path: Path) -> None:
    png = tmp_path / "shot.png"
    preview = tmp_path / "preview.png"
    png.write_bytes(b"png")
    preview.write_bytes(b"preview")
    from vdisplay.application.commands import CommandResult

    result = CommandResult.success(
        action="screenshot",
        data={"path": str(png), "preview": {"preview_path": str(preview)}},
        artifacts=[ArtifactRef(kind="map", path=str(png), label="map.json")],
    )
    artifacts = collect_artifacts(result)
    assert len(artifacts) == 2
    kinds = {artifact.kind for artifact in artifacts}
    assert kinds == {"map", "preview"}


def test_executor_records_control_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    session_dir = tmp_path / "control-session"
    monkeypatch.setenv("VDISPLAY_SESSION_DIR", str(session_dir))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "vdisplay.application.executor.execute_local",
        lambda cmd: {
            "ok": True,
            "diagnostics": {
                "control": {
                    "action": "click",
                    "routing": {"selected_provider": "vision", "why_selected": ["map target"]},
                    "verify": {"verified": True, "mode": "anchor_visible"},
                }
            },
        },
    )

    from vdisplay.application.commands import CommandVerb

    execute(
        CommandRequest(
            verb=CommandVerb.CONTROL_CLICK,
            request_source="cli",
            line="CONTROL CLICK",
        ),
        force_route="local",
    )

    diagnostics = json.loads(
        (session_dir / "steps" / "0001" / "diagnostics.json").read_text(encoding="utf-8")
    )
    assert diagnostics["control"]["routing"]["selected_provider"] == "vision"
    readme = (session_dir / "README.md").read_text(encoding="utf-8")
    assert "diagnostics.json" in readme


def test_executor_records_flat_mock_control_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    session_dir = tmp_path / "flat-mock-session"
    monkeypatch.setenv("VDISPLAY_SESSION_DIR", str(session_dir))
    monkeypatch.setenv("VDISPLAY_EVENT_STORE", "1")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "vdisplay.application.executor.execute_local",
        lambda cmd: {
            "ok": True,
            "action": "invoke",
            "verified": True,
            "target": {"name": "Increment"},
        },
    )

    from vdisplay.application.commands import CommandVerb

    execute(
        CommandRequest(
            verb=CommandVerb.CONTROL_CLICK,
            request_source="cli",
            line="CONTROL CLICK",
        ),
        force_route="local",
    )

    diagnostics = json.loads(
        (session_dir / "steps" / "0001" / "diagnostics.json").read_text(encoding="utf-8")
    )
    control = diagnostics["control"]
    assert control["action"] == "invoke"
    assert control["target"]["name"] == "Increment"
    assert control["verify"]["verified"] is True

    index = (session_dir / "index.jsonl").read_text(encoding="utf-8")
    assert "ControlActionPlanned" in index
    assert "ControlActionExecuted" in index
    assert "ControlVerificationPassed" in index


def test_reprocess_session_diagnostics_backfills_control(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    session_dir = tmp_path / "legacy-session"
    step_dir = session_dir / "steps" / "0001"
    step_dir.mkdir(parents=True)
    session_dir.mkdir(parents=True, exist_ok=True)

    (step_dir / "result.json").write_text(
        json.dumps(
            {
                "ok": True,
                "action": "control_click",
                "data": {
                    "ok": True,
                    "action": "invoke",
                    "verified": True,
                    "target": {"name": "Increment"},
                },
                "diagnostics": {"verify": {"verified": True}},
                "command": "CONTROL_CLICK",
                "request_id": "req-1",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (step_dir / "diagnostics.json").write_text("{}\n", encoding="utf-8")
    (session_dir / "session.json").write_text(
        json.dumps(
            {
                "version": 1,
                "session_id": "legacy",
                "started_at": "2026-06-10T00:00:00Z",
                "updated_at": "2026-06-10T00:00:00Z",
                "source": "cli",
                "route_default": "local",
                "host": "test",
                "cwd": str(tmp_path),
                "pid": 1,
                "env": {},
                "steps": [
                    {
                        "index": 1,
                        "step_id": "0001",
                        "request_id": "req-1",
                        "timestamp": "2026-06-10T00:00:00Z",
                        "duration_ms": 1,
                        "source": "cli",
                        "route": "local",
                        "verb": "CONTROL_CLICK",
                        "action": "control_click",
                        "command_line": "CONTROL_CLICK",
                        "ok": True,
                        "request_path": "steps/0001/request.json",
                        "result_path": "steps/0001/result.json",
                        "artifacts": [],
                        "diagnostics": {},
                    }
                ],
                "summary": {"total_steps": 1, "ok_steps": 1, "failed_steps": 0},
                "maps": [],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (session_dir / "index.jsonl").write_text(
        json.dumps(
            {
                "event_id": "e1",
                "event_type": "StepRecorded",
                "occurred_at_ms": 1,
                "session_id": "legacy",
                "request_id": "req-1",
                "aggregate": "command",
                "body": {
                    "step_id": "0001",
                    "verb": "CONTROL_CLICK",
                    "ok": True,
                    "duration_ms": 1,
                    "request_path": "steps/0001/request.json",
                    "result_path": "steps/0001/result.json",
                    "diagnostics": {},
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    from vdisplay.application.session_recorder import reprocess_session_diagnostics

    report = reprocess_session_diagnostics(session_dir)
    assert report["updated_steps"] == 1
    assert report["added_control_events"] >= 2

    diagnostics = json.loads((step_dir / "diagnostics.json").read_text(encoding="utf-8"))
    assert diagnostics["control"]["action"] == "invoke"
    readme = (session_dir / "README.md").read_text(encoding="utf-8")
    assert "verified `True`" in readme


def test_extract_diagnostics_synthesizes_control_from_flat_mock() -> None:
    from vdisplay.application.commands import CommandResult
    from vdisplay.application.session_recorder import extract_diagnostics

    result = CommandResult.success(
        action="control_click",
        data={
            "ok": True,
            "action": "invoke",
            "verified": True,
            "target": {"name": "Increment"},
        },
    )
    diagnostics = extract_diagnostics(result)
    control = diagnostics["control"]
    assert control["action"] == "invoke"
    assert control["target"]["name"] == "Increment"
    assert control["verify"]["verified"] is True
    assert control["actuation"]["ok"] is True


def test_extract_diagnostics_diagnose_control_backend() -> None:
    from vdisplay.application.commands import CommandResult
    from vdisplay.application.session_recorder import extract_diagnostics

    result = CommandResult.success(
        action="diagnose_control",
        data={"ok": True, "control": {"backend": "atspi"}},
    )
    diagnostics = extract_diagnostics(result)
    assert diagnostics["control"]["routing"]["selected_provider"] == "atspi"


def test_control_events_from_flat_mock_diagnostics() -> None:
    from vdisplay.application.events import control_events_from_diagnostics

    events = control_events_from_diagnostics(
        session_id="sess",
        request_id="req",
        verb="CONTROL_CLICK",
        diagnostics={
            "control": {
                "action": "invoke",
                "target": {"name": "Increment"},
                "verify": {"verified": True},
                "actuation": {"ok": True, "method": "click"},
            }
        },
        ok=True,
    )
    types = [event.event_type for event in events]
    assert "ControlActionPlanned" in types
    assert "ControlActionExecuted" in types
    assert "ControlVerificationPassed" in types


def test_render_readme_includes_routing() -> None:
    from vdisplay.application.session_recorder import SessionDocument, StepRecord

    doc = SessionDocument(
        session_id="test-session",
        started_at="2026-06-10T10:00:00Z",
        updated_at="2026-06-10T10:00:01Z",
        summary={"total_steps": 1, "ok_steps": 1, "failed_steps": 0},
        steps=[
            StepRecord(
                index=1,
                step_id="0001",
                request_id="req-1",
                timestamp="2026-06-10T10:00:01Z",
                duration_ms=12,
                source="dsl",
                route="local",
                verb="CONTROL_CLICK",
                action="control_click",
                command_line="CONTROL CLICK",
                ok=True,
                request_path="steps/0001/request.json",
                result_path="steps/0001/result.json",
                diagnostics={
                    "routing": {
                        "selected_provider": "vision",
                        "why_selected": ["explicit backend=vision"],
                    }
                },
            )
        ],
    )
    readme = render_readme(doc)
    assert "vision" in readme
    assert "CONTROL CLICK" in readme


def test_render_readme_embeds_screenshot_preview(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from vdisplay.application.session_recorder import SessionDocument, StepRecord
    from vdisplay.application.session_recorder_readme import render_readme

    monkeypatch.setenv("VDISPLAY_SESSION_EMBED_IMAGES", "1")
    png = tmp_path / "steps" / "0001" / "shot.png"
    png.parent.mkdir(parents=True)
    png.write_bytes(b"png")
    observe = tmp_path / "observe" / "capture.png"
    observe.parent.mkdir(parents=True)
    observe.write_bytes(b"observe")

    doc = SessionDocument(
        session_id="embed-session",
        started_at="2026-06-10T10:00:00Z",
        updated_at="2026-06-10T10:00:01Z",
        summary={"total_steps": 1, "ok_steps": 1, "failed_steps": 0},
        steps=[
            StepRecord(
                index=1,
                step_id="0001",
                request_id="req-1",
                timestamp="2026-06-10T10:00:01Z",
                duration_ms=1,
                source="cli",
                route="local",
                verb="SCREENSHOT",
                action="screenshot",
                command_line="SCREENSHOT",
                ok=True,
                request_path="steps/0001/request.json",
                result_path="steps/0001/result.json",
                artifacts=[{"kind": "screenshot", "session_path": "steps/0001/shot.png"}],
            )
        ],
    )
    readme = render_readme(doc, session_dir=tmp_path)
    assert "![screenshot](steps/0001/shot.png)" in readme
    assert "![observe capture](observe/capture.png)" in readme
    assert "## Observe capture" in readme
