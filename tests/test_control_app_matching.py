from __future__ import annotations

from vdisplay.control.models import ControlNode, ControlRole
from vdisplay.control.selector import ControlSelector, find_matches, pick_match


def _node(
    node_id: str,
    *,
    role: ControlRole,
    name: str | None = None,
    app_label: str | None = None,
    window_title: str | None = None,
) -> ControlNode:
    return ControlNode(
        id=node_id,
        backend="test",
        role=role,
        name=name,
        app_label=app_label,
        window_title=window_title,
    )


def test_app_matches_process_name() -> None:
    nodes = {
        "a": _node("a", role=ControlRole.BUTTON, name="Increment", app_label="gtk_demo_app.py", window_title="vdisplay-gtk-demo"),
    }
    matches = find_matches(nodes, ControlSelector(role="button", app="gtk_demo_app.py"))
    assert len(matches) == 1


def test_app_matches_window_title() -> None:
    nodes = {
        "a": _node("a", role=ControlRole.BUTTON, name="Increment", app_label="gtk_demo_app.py", window_title="vdisplay-gtk-demo"),
    }
    matches = find_matches(nodes, ControlSelector(role="button", app="vdisplay-gtk-demo"))
    assert len(matches) == 1


def test_window_title_selector() -> None:
    nodes = {
        "a": _node("a", role=ControlRole.BUTTON, name="Save", app_label="editor", window_title="Document - Untitled"),
        "b": _node("b", role=ControlRole.BUTTON, name="Save", app_label="editor", window_title="Settings"),
    }
    picked = pick_match(nodes, ControlSelector(role="button", name="Save", window_title="Document"))
    assert picked is not None
    assert picked.id == "a"
