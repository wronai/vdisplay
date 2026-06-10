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
