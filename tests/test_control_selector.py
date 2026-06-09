from __future__ import annotations

from vdisplay.control.models import ControlBounds, ControlNode, ControlRole
from vdisplay.control.selector import ControlSelector, find_matches, parse_selector, pick_match


def _node(node_id: str, *, role: ControlRole, name: str, app: str = "demo") -> ControlNode:
    return ControlNode(
        id=node_id,
        backend="test",
        role=role,
        name=name,
        app_label=app,
        bounds=ControlBounds(0, 0, 100, 30),
    )


def test_parse_selector_button_name() -> None:
    sel = parse_selector('button[name="Save"]')
    assert sel.role == "button"
    assert sel.name == "Save"


def test_find_and_pick_match() -> None:
    nodes = {
        "a": _node("a", role=ControlRole.BUTTON, name="Cancel"),
        "b": _node("b", role=ControlRole.BUTTON, name="Save"),
        "c": _node("c", role=ControlRole.INPUT, name="Search"),
    }
    selector = ControlSelector(role="button", name="Save")
    matches = find_matches(nodes, selector)
    assert [item.id for item in matches] == ["b"]
    picked = pick_match(nodes, selector)
    assert picked is not None
    assert picked.id == "b"
