from __future__ import annotations

from vdisplay.control.models import ControlBounds, ControlNode, ControlRole
from vdisplay.control.selector import ControlSelector, find_matches, parse_selector


def _node(
    node_id: str,
    *,
    role: ControlRole,
    name: str,
    app: str = "demo",
    text_value: str | None = None,
    provider_ref: str | None = None,
    window_title: str = "",
) -> ControlNode:
    return ControlNode(
        id=node_id,
        backend="test",
        role=role,
        name=name,
        app_label=app,
        window_title=window_title,
        text_value=text_value,
        provider_ref=provider_ref,
        bounds=ControlBounds(0, 0, 100, 30),
    )


def test_selector_roundtrip() -> None:
    selector = ControlSelector(
        role="button",
        name="Save",
        app="demo",
        dom_css="#submit",
        environment="browser",
        terminal_line=3,
        terminal_col=10,
        session_id="pty-demo",
        vision_anchor="login-form",
        extra={"frame": "main"},
    )
    restored = ControlSelector.from_dict(selector.to_dict())
    assert restored.role == "button"
    assert restored.dom_css == "#submit"
    assert restored.environment == "browser"
    assert restored.terminal_line == 3
    assert restored.session_id == "pty-demo"
    assert restored.extra == {"frame": "main"}


def test_parse_css_and_xpath() -> None:
    css = parse_selector("#login")
    assert css.dom_css == "#login"
    assert css.environment == "browser"

    xpath = parse_selector("//button[@type='submit']")
    assert xpath.dom_xpath == "//button[@type='submit']"
    assert xpath.environment == "browser"


def test_parse_window_title_and_text_attrs() -> None:
    sel = parse_selector('button[window_title="Document"][text="OK"]')
    assert sel.role == "button"
    assert sel.window_title == "Document"
    assert sel.text == "OK"


def test_find_by_accessibility_id_and_text() -> None:
    nodes = {
        "a": _node("a", role=ControlRole.BUTTON, name="Go", provider_ref="btn-go"),
        "b": _node("b", role=ControlRole.LABEL, name="Status", text_value="Ready"),
    }
    by_id = find_matches(nodes, ControlSelector(accessibility_id="btn-go"))
    assert [item.id for item in by_id] == ["a"]

    by_text = find_matches(nodes, ControlSelector(text="Ready"))
    assert [item.id for item in by_text] == ["b"]


def test_active_fields_per_environment() -> None:
    browser = ControlSelector(environment="browser", dom_css="#x", role="button")
    assert "dom_css" in browser.active_fields()

    terminal = ControlSelector(environment="terminal", terminal_line=2, text_contains="error")
    assert "terminal_line" in terminal.active_fields()
    assert "text_contains" in terminal.active_fields()
