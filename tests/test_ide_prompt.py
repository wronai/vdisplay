from __future__ import annotations

import pytest

from vdisplay.cli import build_parser, main
from vdisplay.desktop_apps import DESKTOP_APPS
from vdisplay.ide_prompt import open_desktop_app, send_ide_prompt


def test_parser_has_app_and_ide_commands() -> None:
    parser = build_parser()
    kinds = parser._subparsers._group_actions[0].choices  # type: ignore[index]
    assert "app" in kinds
    assert "ide" in kinds


def test_app_list_command(monkeypatch) -> None:
    import io
    import sys

    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    assert main(["app", "list"]) == 0
    payload = __import__("json").loads(captured.getvalue())
    assert "apps" in payload
    assert "count" in payload


def test_ide_list_command(monkeypatch) -> None:
    import io
    import sys

    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    assert main(["ide", "list"]) == 0
    payload = __import__("json").loads(captured.getvalue())
    assert "ides" in payload


def test_open_desktop_app_uses_subprocess(monkeypatch) -> None:
    if "cursor" not in DESKTOP_APPS:
        pytest.skip("cursor not installed on host")

    seen: dict[str, object] = {}

    class FakeProcess:
        pid = 4242

    def fake_popen(argv, **kwargs):
        seen["argv"] = argv
        seen["kwargs"] = kwargs
        return FakeProcess()

    monkeypatch.setattr("vdisplay.ide_prompt.subprocess.Popen", fake_popen)
    monkeypatch.setattr("vdisplay.ide_prompt.time.sleep", lambda _seconds: None)

    result = open_desktop_app("cursor", wait_seconds=0.0)
    assert result["ok"] is True
    assert result["pid"] == 4242
    assert seen["argv"]


def test_send_ide_prompt_happy_path(monkeypatch) -> None:
    if "cursor" not in DESKTOP_APPS:
        pytest.skip("cursor not installed on host")

    monkeypatch.setattr(
        "vdisplay.ide_prompt.wait_for_app_window",
        lambda *args, **kwargs: {"ok": True, "focused": True},
    )

    def fake_find(**kwargs):
        return {
            "ok": True,
            "count": 1,
            "selected": {"id": "chat-input-1", "role": "input"},
        }

    def fake_set_value(**kwargs):
        assert kwargs["value"] == "hello"
        return {"ok": True, "action": "set_value"}

    monkeypatch.setattr("vdisplay.application.services.control.controls_find", fake_find)
    monkeypatch.setattr("vdisplay.application.services.control.control_set_value", fake_set_value)

    result = send_ide_prompt(app_id="cursor", text="hello", wait_window=True)
    assert result["ok"] is True
    assert result["typed"]["action"] == "set_value"


def test_send_ide_prompt_no_match(monkeypatch) -> None:
    if "cursor" not in DESKTOP_APPS:
        pytest.skip("cursor not installed on host")

    monkeypatch.setattr(
        "vdisplay.ide_prompt.wait_for_app_window",
        lambda *args, **kwargs: {"ok": True, "focused": True},
    )
    monkeypatch.setattr(
        "vdisplay.application.services.control.controls_find",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("no match")),
    )

    result = send_ide_prompt(app_id="cursor", text="hello")
    assert result["ok"] is False
    assert "no chat input matched" in result["message"]
