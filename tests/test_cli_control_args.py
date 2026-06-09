from __future__ import annotations

from vdisplay.application.services.control import _selector_from_kwargs
from vdisplay.cli import build_parser, main


def test_control_list_accepts_session_id() -> None:
    parser = build_parser()
    args = parser.parse_args(["control", "list", "--backend", "browser", "--session-id", "web-1"])
    assert args.action == "list"
    assert args.backend == "browser"
    assert args.session_id == "web-1"


def test_diagnose_control_accepts_selector_and_session_id() -> None:
    parser = build_parser()
    args = parser.parse_args(
        ["diagnose", "control", "--selector", "#go", "--session-id", "web-1"]
    )
    assert args.aspect == "control"
    assert args.selector == "#go"
    assert args.session_id == "web-1"


def test_selector_from_kwargs_merges_session_id_after_css_parse() -> None:
    selector = _selector_from_kwargs(selector="#go", session_id="web-1", backend="browser")
    assert selector.dom_css == "#go"
    assert selector.session_id == "web-1"
    assert selector.environment == "browser"


def test_control_browser_open_parser() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "control",
            "browser-open",
            "--url",
            "https://example.com",
            "--session-id",
            "web-1",
            "--headed",
        ]
    )
    assert args.action == "browser-open"
    assert args.url == "https://example.com"
    assert args.session_id == "web-1"
    assert args.headed is True


def test_control_click_does_not_duplicate_backend(monkeypatch) -> None:
    seen: dict[str, object] = {}

    def fake_click(**kwargs):
        seen.update(kwargs)
        return {"ok": True}

    monkeypatch.setattr("vdisplay.commands.control.control_svc.control_click", fake_click)

    import io
    import sys

    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    assert (
        main(
            [
                "control",
                "click",
                "--backend",
                "x11",
                "--app",
                "firefox",
                "--role",
                "button",
                "--name",
                "Reload",
            ]
        )
        == 0
    )
    assert seen.get("backend") == "x11"
    assert seen.get("app") == "firefox"


def test_control_list_invokes_service_with_session_id(monkeypatch) -> None:
    seen: dict[str, object] = {}

    def fake_list(**kwargs):
        seen.update(kwargs)
        return {"ok": True, "nodes": {}}

    monkeypatch.setattr("vdisplay.commands.control.control_svc.controls_list", fake_list)

    import io
    import sys

    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    assert main(["control", "list", "--backend", "browser", "--session-id", "web-1"]) == 0
    assert seen.get("session_id") == "web-1"
    assert seen.get("backend") == "browser"
