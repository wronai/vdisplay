"""CLI session flags and artifact builders."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vdisplay.application.artifacts import artifacts_from_control, artifacts_from_screenshot, build_artifacts
from vdisplay.application.commands import ArtifactRef, CommandRequest, CommandVerb
from vdisplay.application.session_context import apply_cli_session_args, enrich_command_request
from vdisplay.cli import build_parser, main


def test_root_parser_accepts_audit_session_flags() -> None:
    parser = build_parser()
    args = parser.parse_args(["--session", "--session-id", "pycharm-chat", "monitors"])
    assert args.session is True
    assert args.audit_session_id == "pycharm-chat"
    assert args.kind == "monitors"


def test_apply_cli_session_args_sets_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VDISPLAY_SESSION", raising=False)
    monkeypatch.delenv("VDISPLAY_SESSION_ID", raising=False)
    parser = build_parser()
    args = parser.parse_args(["--session", "--session-id", "demo", "monitors"])
    apply_cli_session_args(args)
    assert __import__("os").environ["VDISPLAY_SESSION"] == "1"
    assert __import__("os").environ["VDISPLAY_SESSION_ID"] == "demo"


def test_enrich_command_request_uses_env_session_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_SESSION_ID", "from-env")
    cmd = enrich_command_request(CommandRequest(verb=CommandVerb.MONITORS))
    assert cmd.session_id == "from-env"
    assert cmd.request_id


def test_artifacts_from_screenshot_paths(tmp_path: Path) -> None:
    png = tmp_path / "screen.png"
    png.write_bytes(b"png")
    refs = artifacts_from_screenshot({"path": str(png), "mode": "host"})
    assert len(refs) == 1
    assert refs[0].kind == "screenshot"


def test_artifacts_from_control_preview_and_diff(tmp_path: Path) -> None:
    preview = tmp_path / "preview.png"
    before = tmp_path / "before.png"
    after = tmp_path / "after.png"
    preview.write_bytes(b"p")
    before.write_bytes(b"b")
    after.write_bytes(b"a")
    refs = artifacts_from_control(
        {
            "preview": {"preview_path": str(preview)},
            "artifacts": {"before": str(before), "after": str(after)},
        }
    )
    kinds = {ref.kind for ref in refs}
    assert kinds == {"preview", "before", "after"}


def test_executor_records_control_cli_step(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    session_dir = tmp_path / "control-session"
    monkeypatch.setenv("VDISPLAY_SESSION_DIR", str(session_dir))
    monkeypatch.chdir(tmp_path)

    def fake_find(**kwargs):
        return {"ok": True, "count": 1, "matches": [], "selected": {"id": "n1"}}

    monkeypatch.setattr("vdisplay.application.services.control.controls_find", fake_find)

    import io
    import sys

    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    assert (
        main(
            [
                "control",
                "find",
                "--backend",
                "vision",
                "--text-contains",
                "Ask",
            ]
        )
        == 0
    )
    assert (session_dir / "steps" / "0001" / "result.json").is_file()
    payload = json.loads((session_dir / "steps" / "0001" / "request.json").read_text(encoding="utf-8"))
    assert payload["verb"] == "CONTROLS_FIND"
    assert payload["request_source"] == "cli"


def test_build_artifacts_for_screenshot_verb(tmp_path: Path) -> None:
    png = tmp_path / "out.png"
    png.write_bytes(b"x")
    cmd = CommandRequest(verb=CommandVerb.SCREENSHOT)
    refs = build_artifacts(cmd, {"saved": str(png)})
    assert refs == [ArtifactRef(kind="screenshot", path=str(png), label="saved")]
