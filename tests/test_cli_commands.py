from __future__ import annotations

import json

from vdisplay.cli import build_parser, main
from vdisplay.payloads import monitors_payload, windows_payload


def test_parser_has_discovery_commands() -> None:
    parser = build_parser()
    kinds = parser._subparsers._group_actions[0].choices  # type: ignore[index]
    assert "monitors" in kinds
    assert "windows" in kinds
    assert "all" in kinds
    assert "nlp" in kinds
    assert "outputs" in kinds


def test_monitors_command_registered() -> None:
    parser = build_parser()
    kinds = parser._subparsers._group_actions[0].choices  # type: ignore[index]
    assert kinds["monitors"].prog.endswith("monitors")


def test_windows_defaults_to_include_all(monkeypatch) -> None:
    seen: dict[str, bool] = {}

    def fake_windows(display=None, **kwargs):
        seen.update(kwargs)
        return {"window_count": 0, "windows": []}

    monkeypatch.setattr("vdisplay.application.services.discovery.list_windows_payload", fake_windows)

    import io
    import sys

    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    assert main(["windows"]) == 0
    assert seen.get("include_all") is True


def test_windows_apps_only_flag(monkeypatch) -> None:
    seen: dict[str, bool] = {}

    def fake_windows(display=None, **kwargs):
        seen.update(kwargs)
        return {"window_count": 0, "windows": []}

    monkeypatch.setattr("vdisplay.application.services.discovery.list_windows_payload", fake_windows)

    import io
    import sys

    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    assert main(["windows", "--apps-only"]) == 0
    assert seen.get("include_all") is False


def test_payload_defaults_include_all() -> None:
    import inspect

    monitors_sig = inspect.signature(monitors_payload)
    windows_sig = inspect.signature(windows_payload)
    assert monitors_sig.parameters["include_all"].default is True
    assert windows_sig.parameters["include_all"].default is True


def test_all_command_structure(monkeypatch) -> None:
    monkeypatch.setattr(
        "vdisplay.application.services.discovery.list_all",
        lambda display=None, **kwargs: {
            "requested_display": display,
            "resolved_display": ":0",
            "monitor_count": 1,
            "window_count": 1,
            "adopted_count": 0,
            "monitors": [{"name": "DP-1", "nl": "monitor DP-1"}],
            "windows": [{"window_id": "1", "nl": "app window"}],
            "adopted": [],
        },
    )

    import io
    import sys

    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    assert main(["all"]) == 0
    payload = json.loads(captured.getvalue())
    assert "monitors" in payload
    assert "windows" in payload
    assert "adopted" in payload
    assert payload["monitor_count"] == 1
    assert payload["window_count"] == 1
