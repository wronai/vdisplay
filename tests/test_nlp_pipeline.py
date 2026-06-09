from __future__ import annotations

import json

from vdisplay.nlp import nl_to_dsl, run_nl_prompt


def test_nl_to_dsl_monitors_on_display_zero() -> None:
    assert nl_to_dsl("list monitors on display zero") == "MONITORS DISPLAY :0"


def test_nl_to_dsl_windows() -> None:
    assert nl_to_dsl("show application windows on display zero") == "WINDOWS DISPLAY :0"


def test_run_nl_prompt_dsl_only() -> None:
    line, output, code = run_nl_prompt("list monitors on display zero", dsl_only=True)
    assert line == "MONITORS DISPLAY :0"
    assert output == "MONITORS DISPLAY :0"
    assert code == 0


def test_run_nl_prompt_full_pipeline(monkeypatch) -> None:
    from vdisplay.application.commands import CommandResult

    sample = {
        "requested_display": ":0",
        "resolved_display": ":0",
        "monitor_count": 1,
        "monitors": [{"name": "DP-1", "monitor_id": 0, "nl": "monitor DP-1"}],
    }

    def fake_execute(request, **kwargs):
        return CommandResult.success(action=request.action, data=sample, command=request.line)

    monkeypatch.setattr("vdisplay.application.executor.execute", fake_execute)

    line, output, code = run_nl_prompt("list monitors on display zero", dsl_only=False)
    assert line == "MONITORS DISPLAY :0"
    assert code == 0
    payload = json.loads(output or "{}")
    assert payload["monitor_count"] == 1
    assert payload["monitors"][0]["monitor_id"] == 0


def test_dsl2vdisplay_monitors_matches_payload(monkeypatch) -> None:
    sample = {
        "requested_display": ":0",
        "resolved_display": ":0",
        "monitor_count": 2,
        "monitors": [{"name": "DP-1"}, {"name": "DP-2"}],
    }
    from vdisplay.application.commands import CommandResult

    def fake_execute(request, **kwargs):
        return CommandResult.success(action=request.action, data=sample, command=request.line)

    monkeypatch.setattr("vdisplay.application.executor.execute", fake_execute)

    from dsl2vdisplay import dispatch

    result = dispatch("MONITORS DISPLAY :0")
    assert result.ok is True
    assert result.action == "monitors"
    assert result.data == sample
    assert json.loads(result.output or "{}") == sample
