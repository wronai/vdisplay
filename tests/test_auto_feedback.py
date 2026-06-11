from __future__ import annotations

import pytest

from vdisplay.application.auto.feedback import (
    finalize_result_ok,
    is_control_command,
    parse_verify_from_output,
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

    result = ExecuteResult(ok=True, method="vdisplay-cli", output='{"verified": false}')
    feedback = TaskFeedback(verify_requested=True)
    assert finalize_result_ok(result, feedback) is False
    assert feedback.verify_passed is False


def test_is_control_command() -> None:
    assert is_control_command("vdisplay control find --backend vision")
    assert is_control_command("CONTROL_CLICK ROLE button")
    assert not is_control_command("vdisplay monitors")
