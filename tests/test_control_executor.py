from __future__ import annotations

import pytest

from vdisplay.application.commands import CommandRequest, CommandVerb
from vdisplay.application.executor import execute


def test_executor_control_click_local(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "vdisplay.application.services.control.control_click",
        lambda **kwargs: {
            "ok": True,
            "action": "invoke",
            "verified": True,
            "target": {"name": "Increment"},
        },
    )
    result = execute(
        CommandRequest(
            verb=CommandVerb.CONTROL_CLICK,
            control_role="button",
            control_name="Increment",
            control_app="vdisplay-gtk-demo",
            control_verify=True,
            line="CONTROL_CLICK",
        ),
        force_route="local",
    )
    assert result.ok is True
    assert result.action == "control_click"
    assert result.data["verified"] is True


def test_executor_controls_find_local(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "vdisplay.application.services.control.controls_find",
        lambda **kwargs: {
            "ok": True,
            "selected": {"name": "Increment", "role": "button"},
            "count": 1,
        },
    )
    result = execute(
        CommandRequest(
            verb=CommandVerb.CONTROLS_FIND,
            control_role="button",
            control_name="Increment",
            control_app="gtk_demo_app.py",
            line="CONTROLS_FIND",
        ),
        force_route="local",
    )
    assert result.ok is True
    assert result.action == "controls_find"
    assert result.data["selected"]["name"] == "Increment"


def test_executor_diagnose_control_local(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "vdisplay.application.services.control.diagnose_control",
        lambda **kwargs: {"ok": True, "control": {"backend": "atspi"}},
    )
    result = execute(
        CommandRequest(verb=CommandVerb.DIAGNOSE_CONTROL, line="DIAGNOSE_CONTROL"),
        force_route="local",
    )
    assert result.ok is True
    assert result.action == "diagnose_control"
    assert result.data["control"]["backend"] == "atspi"
