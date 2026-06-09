from __future__ import annotations

from vdisplay.application.commands import CommandRequest, CommandResult, CommandVerb
from vdisplay.application.errors import ApplicationError, ErrorCode


def test_command_request_from_dsl_monitors() -> None:
    req = CommandRequest.from_dsl({"verb": "MONITORS", "display": ":0"}, line="MONITORS DISPLAY :0")
    assert req.verb == CommandVerb.MONITORS
    assert req.display == ":0"
    assert req.action == "monitors"


def test_command_request_from_dsl_apps_only() -> None:
    req = CommandRequest.from_dsl({"verb": "WINDOWS", "apps_only": True})
    assert req.apps_only is True
    assert req.include_all is False


def test_command_result_envelope_success() -> None:
    result = CommandResult.success(
        action="health",
        data={"status": "ok"},
        meta={"route": "local"},
    )
    payload = result.to_dict()
    assert payload["ok"] is True
    assert payload["data"]["status"] == "ok"
    assert payload["meta"]["route"] == "local"
    assert "error" not in payload


def test_command_result_envelope_failure() -> None:
    result = CommandResult.failure(
        action="screenshot",
        error=ApplicationError(ErrorCode.BACKEND_UNAVAILABLE, "capture failed"),
    )
    payload = result.to_dict()
    assert payload["ok"] is False
    assert payload["error"]["code"] == "backend_unavailable"
    assert payload["error"]["message"] == "capture failed"


def test_command_result_to_dsl_result() -> None:
    result = CommandResult.success(action="monitors", data={"monitor_count": 0}, command="MONITORS")
    dsl = result.to_dsl_result()
    assert dsl.ok is True
    assert dsl.action == "monitors"
    assert dsl.data["monitor_count"] == 0
