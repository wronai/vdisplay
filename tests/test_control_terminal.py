from __future__ import annotations

from vdisplay.application.services import control as control_svc
from vdisplay.control.engine import resolve_provider
from vdisplay.control.providers.terminal import TerminalControlProvider
from vdisplay.control.providers.terminal_screen import ScreenBuffer, nodes_from_screen
from vdisplay.control.providers.terminal_session import TerminalSessionRegistry, default_registry
from vdisplay.control.selector import ControlSelector, parse_selector, pick_match
from vdisplay.exceptions import BackendNotAvailableError


def _demo_registry() -> TerminalSessionRegistry:
    registry = TerminalSessionRegistry()
    registry.open_mock(
        session_id="demo",
        lines=[
            "Welcome to vdisplay terminal",
            "Name: ",
            "[ OK ]  [ Cancel ]",
        ],
        cursor_row=1,
        cursor_col=7,
        title="demo-shell",
    )
    return registry


def _seed_default_demo() -> None:
    default_registry().close_all()
    default_registry().open_mock(
        session_id="demo",
        lines=[
            "Welcome to vdisplay terminal",
            "Name: ",
            "[ OK ]  [ Cancel ]",
        ],
        cursor_row=1,
        cursor_col=7,
        title="demo-shell",
    )


def test_terminal_screen_nodes() -> None:
    buffer = ScreenBuffer(rows=5, cols=40, title="test")
    buffer.set_lines(["hello", "world"], cursor_row=1, cursor_col=3)
    snapshot = nodes_from_screen(buffer.snapshot(), session_id="demo")
    assert len(snapshot.nodes) >= 3
    line_nodes = [
        node
        for node in snapshot.nodes.values()
        if node.state.get("terminal_line") == 2 and node.role.value == "label"
    ]
    assert len(line_nodes) == 1
    assert line_nodes[0].text_value == "world"


def test_terminal_provider_snapshot_and_find() -> None:
    registry = _demo_registry()
    provider = TerminalControlProvider(session_id="demo", registry=registry)
    snapshot = provider.snapshot()
    assert snapshot.backend == "terminal"
    assert any(node.text_value and "OK" in node.text_value for node in snapshot.nodes.values())

    by_line = provider.find(ControlSelector(terminal_line=3, environment="terminal"))
    assert len(by_line) >= 1
    assert "OK" in (by_line[0].text_value or "")

    by_text = provider.find(ControlSelector(text_contains="Cancel", environment="terminal"))
    assert len(by_text) >= 1


def test_terminal_provider_actions() -> None:
    registry = _demo_registry()
    provider = TerminalControlProvider(session_id="demo", registry=registry)
    snapshot = provider.snapshot()
    cursor = snapshot.nodes[f"terminal:demo:cursor"]

    typed = provider.set_value(cursor.id, "Alice")
    assert typed["ok"] is True
    assert registry.require("demo").sent_text() == ["Alice"]

    invoked = provider.invoke(f"terminal:demo:line:3")
    assert invoked["ok"] is True
    assert registry.require("demo").sent_text()[-1] == "\r"


def test_terminal_selector_parse_and_match() -> None:
    selector = parse_selector('line[2][text="Name:"]')
    assert selector.terminal_line == 2
    assert selector.text == "Name:"
    assert selector.environment == "terminal"

    registry = _demo_registry()
    provider = TerminalControlProvider(session_id="demo", registry=registry)
    snapshot = provider.snapshot()
    target = pick_match(snapshot.nodes, selector)
    assert target is not None
    assert target.text_value == "Name:"


def test_terminal_service_set_value() -> None:
    _seed_default_demo()
    cursor_id = f"terminal:demo:cursor"

    result = control_svc._execute_action(
        action="set_value",
        display=None,
        backend="terminal",
        verify=False,
        screenshot_verify=False,
        value="Bob",
        session_id="demo",
        role="input",
        environment="terminal",
    )
    assert result["ok"] is True
    assert default_registry().require("demo").sent_text() == ["Bob"]
    assert result["target"]["id"] == cursor_id
    default_registry().close_all()


def test_terminal_service_verify_text_change() -> None:
    default_registry().close_all()
    default_registry().open_mock(
        session_id="demo",
        lines=[""],
        cursor_row=0,
        cursor_col=0,
    )

    result = control_svc._execute_action(
        action="set_value",
        display=None,
        backend="terminal",
        verify=True,
        screenshot_verify=False,
        value="hello",
        session_id="demo",
        environment="terminal",
        role="input",
    )
    assert result["verified"] is True
    assert result["state_diff"]["text_value"]["after"] == "hello"
    default_registry().close_all()


def test_resolve_provider_terminal_backend() -> None:
    _seed_default_demo()
    resolved = resolve_provider("terminal", session_id="demo")
    assert resolved.name == "terminal"
    default_registry().close_all()


def test_resolve_provider_auto_routes_terminal_environment() -> None:
    _seed_default_demo()
    provider = resolve_provider(
        "auto",
        session_id="demo",
        selector=ControlSelector(environment="terminal"),
    )
    assert provider.name == "terminal"
    default_registry().close_all()


def test_resolve_provider_unknown_backend() -> None:
    try:
        resolve_provider("not-a-backend")
    except BackendNotAvailableError as exc:
        assert "unknown" in str(exc).lower()
    else:
        raise AssertionError("expected BackendNotAvailableError")


def test_terminal_service_missing_session_raises() -> None:
    registry = TerminalSessionRegistry()
    provider = TerminalControlProvider(session_id="missing", registry=registry)
    try:
        provider.snapshot()
    except (RuntimeError, KeyError):
        return
    raise AssertionError("expected missing session error")
