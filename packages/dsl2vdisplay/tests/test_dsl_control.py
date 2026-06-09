from __future__ import annotations

import pytest

from dsl2vdisplay import dispatch
from dsl2vdisplay.grammar import parse_line, to_text
from dsl2vdisplay.schema_registry import validate_command_dict

from vdisplay.application.commands import CommandRequest, CommandResult


def test_parse_controls_list_uppercase() -> None:
    cmd = parse_line("CONTROLS_LIST APP vdisplay-gtk-demo BACKEND atspi MAX_DEPTH 4")
    assert cmd is not None
    assert cmd["verb"] == "CONTROLS_LIST"
    assert cmd["app"] == "vdisplay-gtk-demo"
    assert cmd["control_backend"] == "atspi"
    assert cmd["max_depth"] == 4
    assert validate_command_dict(cmd) == []


def test_parse_controls_list_human_readable() -> None:
    cmd = parse_line('controls list --app "vdisplay-gtk-demo" --backend atspi')
    assert cmd is not None
    assert cmd["verb"] == "CONTROLS_LIST"
    assert cmd["app"] == "vdisplay-gtk-demo"
    assert cmd["control_backend"] == "atspi"
    assert validate_command_dict(cmd) == []


def test_parse_control_click_with_verify() -> None:
    cmd = parse_line('control click --role button --name Increment --app vdisplay-gtk-demo --verify')
    assert cmd is not None
    assert cmd["verb"] == "CONTROL_CLICK"
    assert cmd["role"] == "button"
    assert cmd["name"] == "Increment"
    assert cmd["app"] == "vdisplay-gtk-demo"
    assert cmd["verify"] is True
    assert validate_command_dict(cmd) == []


def test_parse_control_click_with_screenshot_verify() -> None:
    cmd = parse_line("control click --role button --name Go --screenshot-verify")
    assert cmd is not None
    assert cmd["screenshot_verify"] is True
    request = CommandRequest.from_dsl(cmd)
    assert request.control_screenshot_verify is True
    assert validate_command_dict(cmd) == []


def test_parse_control_set_value_requires_value_schema() -> None:
    missing = parse_line("control set-value --role input --app demo")
    assert missing is not None
    assert validate_command_dict(missing)

    cmd = parse_line('control set-value --role input --app demo --value hello')
    assert cmd is not None
    assert cmd["value"] == "hello"
    assert validate_command_dict(cmd) == []


def test_parse_controls_find_with_provider_ref() -> None:
    cmd = parse_line('controls find --provider-ref /org/gtk/Button/1 --app demo')
    assert cmd is not None
    assert cmd["verb"] == "CONTROLS_FIND"
    assert cmd["provider_ref"] == "/org/gtk/Button/1"
    assert validate_command_dict(cmd) == []


def test_command_request_from_dsl_control() -> None:
    cmd = parse_line('control focus --role input --name Search --app demo --backend atspi --verify')
    assert cmd is not None
    request = CommandRequest.from_dsl(cmd, line="control focus ...")
    assert request.verb.value == "CONTROL_FOCUS"
    assert request.control_role == "input"
    assert request.control_name == "Search"
    assert request.control_app == "demo"
    assert request.control_backend == "atspi"
    assert request.control_verify is True


def test_command_request_provider_ref() -> None:
    cmd = parse_line("control click --id /org/gtk/Button/1 --app demo")
    assert cmd is not None
    request = CommandRequest.from_dsl(cmd)
    assert request.control_provider_ref == "/org/gtk/Button/1"


def test_parse_control_terminal_fields() -> None:
    cmd = parse_line(
        'controls find --backend terminal --session-id demo --environment terminal '
        '--terminal-line 2 --text READY'
    )
    assert cmd is not None
    assert cmd["verb"] == "CONTROLS_FIND"
    assert cmd["control_backend"] == "terminal"
    assert cmd["session_id"] == "demo"
    assert cmd["environment"] == "terminal"
    assert cmd["terminal_line"] == 2
    assert cmd["text"] == "READY"
    assert validate_command_dict(cmd) == []

    request = CommandRequest.from_dsl(cmd)
    assert request.control_session_id == "demo"
    assert request.control_environment == "terminal"
    assert request.control_terminal_line == 2
    assert request.control_text == "READY"


def test_parse_control_terminal_uppercase_flags() -> None:
    cmd = parse_line("CONTROL_SET_VALUE SESSION_ID demo ENVIRONMENT terminal ROLE input VALUE hello")
    assert cmd is not None
    assert cmd["session_id"] == "demo"
    assert cmd["environment"] == "terminal"
    assert cmd["role"] == "input"
    assert cmd["value"] == "hello"
    assert validate_command_dict(cmd) == []


def test_to_text_roundtrip_terminal_control() -> None:
    cmd = parse_line(
        'control set-value --backend terminal --session-id demo --role input --value hello --verify'
    )
    assert cmd is not None
    text = to_text(cmd)
    assert "--backend terminal" in text
    assert "--session-id demo" in text
    assert '--value hello' in text
    assert "--verify" in text


def test_to_text_roundtrip_control_click() -> None:
    cmd = parse_line('control click --role button --name Increment --app demo --verify')
    assert cmd is not None
    text = to_text(cmd)
    assert text.startswith("control click")
    assert "--role button" in text
    assert "--verify" in text


@pytest.mark.parametrize(
    ("line", "action"),
    [
        ('controls list --app demo', "controls_list"),
        ('controls find --role button --name Save --app demo', "controls_find"),
        ('control click --role button --name Increment --app demo --verify', "control_click"),
        ('control focus --role input --app demo', "control_focus"),
        ('control set-value --role input --app demo --value abc', "control_set_value"),
        (
            'control set-value --backend terminal --session-id demo --role input --value hello',
            "control_set_value",
        ),
        ("diagnose control", "diagnose_control"),
    ],
)
def test_dispatch_control_verbs_via_executor(monkeypatch: pytest.MonkeyPatch, line: str, action: str) -> None:
    calls: list[str] = []

    def fake_execute(request, **kwargs):
        calls.append(request.action)
        return CommandResult.success(action=request.action, data={"ok": True})

    import vdisplay.application.executor as executor_mod

    monkeypatch.setattr(executor_mod, "execute", fake_execute)
    result = dispatch(line)
    assert result.ok is True
    assert result.action == action
    assert calls == [action]
