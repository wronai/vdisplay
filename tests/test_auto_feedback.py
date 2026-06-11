from __future__ import annotations

import os
from pathlib import Path

import pytest

from vdisplay.application.auto.feedback import (
    TaskFeedback,
    finalize_result_ok,
    is_control_command,
    parse_verify_from_output,
    post_act_verify_screenshot,
    preflight_actuation,
    prepare_command,
)
from vdisplay.application.auto.tasks import AutoTask


def test_prepare_command_adds_verify_and_map() -> None:
    task = AutoTask(
        id="t1",
        title="click",
        command="vdisplay control click --target chat",
        source="yaml",
        verify=True,
        map_path="maps/chat.json",
        monitor="DP-1",
    )
    cmd, feedback = prepare_command(task.command, task)
    assert "--verify" in cmd
    assert "--map maps/chat.json" in cmd
    assert feedback.verify_requested is True


def test_prepare_command_adds_source_to_screenshot() -> None:
    task = AutoTask(
        id="t2",
        title="shot",
        command="vdisplay screenshot -o /tmp/x.png",
        source="yaml",
        monitor="DP-2",
    )
    cmd, _ = prepare_command(task.command, task)
    assert "--source DP-2" in cmd


def test_parse_verify_from_output() -> None:
    assert parse_verify_from_output('{"ok": true, "verified": true}') is True
    assert parse_verify_from_output('{"verified": false}') is False
    assert parse_verify_from_output('{"ok": true}') is None


def test_finalize_result_ok_respects_verify() -> None:
    from vdisplay.application.auto.executor import ExecuteResult
    from vdisplay.application.auto.feedback import TaskFeedback
    from vdisplay.application.project_config import AutomationDefaults, ProjectConfig

    result = ExecuteResult(ok=True, method="vdisplay-cli", output='{"verified": false}')
    feedback = TaskFeedback(verify_requested=True)
    config = ProjectConfig(automation=AutomationDefaults(verify_strict=False))
    assert finalize_result_ok(result, feedback, config=config) is False
    assert feedback.verify_passed is False


def test_is_control_command() -> None:
    assert is_control_command("vdisplay control find --backend vision")
    assert is_control_command("CONTROL_CLICK ROLE button")
    assert not is_control_command("vdisplay monitors")


def test_copy_sidecar_same_path_sidecar(tmp_path: Path) -> None:
    from vdisplay.application.auto.metadata import copy_sidecar

    png = tmp_path / "task.png"
    png.write_bytes(b"png")
    sidecar = png.with_suffix(".png.context.json")
    sidecar.write_text("{}", encoding="utf-8")
    copied = copy_sidecar(png, png)
    assert str(png) in copied
    assert sidecar.is_file()


def test_post_act_verify_screenshot(tmp_path) -> None:
    from vdisplay.application.auto.executor import ExecuteResult
    from vdisplay.application.project_config import load_project_config

    (tmp_path / "vdisplay.yaml").write_text(
        """
automation:
  post_act_verify: true
  metadata_dir: .vdisplay
""",
        encoding="utf-8",
    )
    config = load_project_config(tmp_path)
    task = AutoTask(
        id="act1",
        title="focus",
        command="vdisplay control focus --backend vision",
        source="yaml",
        monitor="DP-1",
        verify=True,
    )
    feedback = TaskFeedback(
        prepared_command=task.command,
        verify_requested=True,
        verify_passed=True,
    )
    png = tmp_path / ".vdisplay" / "observe" / "act1-post-verify.png"
    png.parent.mkdir(parents=True, exist_ok=True)

    def execute_fn(cmd: str, **kwargs):
        png.write_bytes(b"png")
        return ExecuteResult(ok=True, method="mock", output='{"path": "' + str(png) + '"}')

    post_act_verify_screenshot(feedback, task, config=config, execute_fn=execute_fn)
    assert feedback.post_verify_path == str(png)
    assert png.is_file()


def test_preflight_actuation_fails_without_ocr_or_map(tmp_path, monkeypatch) -> None:
    from vdisplay.application.project_config import AutomationDefaults, ProjectConfig

    monkeypatch.setattr(
        "vdisplay.control.vision_ocr.ocr_available",
        lambda: (False, "pytesseract not installed"),
    )
    config = ProjectConfig(automation=AutomationDefaults(reject_vision_stubs=True))
    task = AutoTask(
        id="act1",
        title="focus",
        command="vdisplay control focus --backend vision",
        source="yaml",
        monitor="DP-1",
    )
    feedback = TaskFeedback()
    cmd = "vdisplay control focus --backend vision --vision-anchor Chat"
    assert preflight_actuation(task, feedback, prepared_command=cmd, config=config) is False
    assert any("actuation preflight failed" in note for note in feedback.notes)


def test_preflight_actuation_passes_with_map(tmp_path) -> None:
    from vdisplay.application.project_config import ProjectConfig

    map_file = tmp_path / "maps" / "cursor-chat.json"
    map_file.parent.mkdir(parents=True)
    map_file.write_text('{"version": 1}', encoding="utf-8")
    config = ProjectConfig(root=tmp_path)
    task = AutoTask(
        id="act1",
        title="focus",
        command="vdisplay control focus",
        source="yaml",
        map_path=str(map_file),
    )
    feedback = TaskFeedback()
    assert preflight_actuation(task, feedback, prepared_command=task.command, config=config) is True
    assert any("map" in note for note in feedback.notes)


def test_task_execution_env_sets_koru_instance(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.application.auto.feedback import task_execution_env

    monkeypatch.delenv("KORU_AUTOPILOT_INSTANCE", raising=False)
    monkeypatch.delenv("KORU_AUTOPILOT_SOCKET", raising=False)
    task = AutoTask(
        id="k1",
        title="koru",
        command="koru autopilot drive --ide jetbrains --no-submit --prompt hi",
        source="yaml",
        raw={"koru_instance": "jetbrains"},
    )
    feedback = TaskFeedback()
    with task_execution_env(task, feedback):
        assert os.environ.get("KORU_AUTOPILOT_INSTANCE") == "jetbrains"
        assert os.environ.get("KORU_AUTOPILOT_SOCKET", "").endswith("koru-autopilot-jetbrains.sock")
    assert os.environ.get("KORU_AUTOPILOT_INSTANCE") is None
