from __future__ import annotations

from vdisplay.control.models import ControlNode, ControlRole, ControlSnapshot
from vdisplay.control.verify import (
    collect_changed_nodes,
    diff_snapshots,
    snapshot_diff,
    verify_action_result,
)


def _node(
    node_id: str,
    *,
    role: ControlRole,
    name: str | None = None,
    text_value: str | None = None,
    parent_id: str | None = None,
    children_ids: list[str] | None = None,
    state: dict | None = None,
) -> ControlNode:
    return ControlNode(
        id=node_id,
        backend="test",
        role=role,
        name=name,
        text_value=text_value,
        parent_id=parent_id,
        children_ids=list(children_ids or []),
        app_label="gtk_demo_app.py",
        state=state or {},
    )


def _gtk_demo_snapshots() -> tuple[ControlSnapshot, ControlSnapshot, ControlNode]:
    before_nodes = {
        "panel": _node("panel", role=ControlRole.PANEL, name="box", children_ids=["label", "button"]),
        "label": _node(
            "label",
            role=ControlRole.LABEL,
            name="counter-label",
            text_value="Count: 0",
            parent_id="panel",
        ),
        "button": _node(
            "button",
            role=ControlRole.BUTTON,
            name="Increment",
            parent_id="panel",
        ),
    }
    after_nodes = {
        "panel": _node("panel", role=ControlRole.PANEL, name="box", children_ids=["label", "button"]),
        "label": _node(
            "label",
            role=ControlRole.LABEL,
            name="counter-label",
            text_value="Count: 1",
            parent_id="panel",
        ),
        "button": _node(
            "button",
            role=ControlRole.BUTTON,
            name="Increment",
            parent_id="panel",
        ),
    }
    before = ControlSnapshot(backend="test", window_id=None, app_label="gtk_demo_app.py", nodes=before_nodes, root_ids=["panel"])
    after = ControlSnapshot(backend="test", window_id=None, app_label="gtk_demo_app.py", nodes=after_nodes, root_ids=["panel"])
    return before, after, before_nodes["button"]


def test_diff_snapshots_detects_label_change() -> None:
    before, after, _ = _gtk_demo_snapshots()
    diff = diff_snapshots(before, after, scope_root_id="panel")
    assert len(diff["text_value_changes"]) == 1
    assert diff["text_value_changes"][0]["name"] == "counter-label"
    assert diff["text_value_changes"][0]["before"] == "Count: 0"
    assert diff["text_value_changes"][0]["after"] == "Count: 1"


def test_verify_click_detects_sibling_label_change() -> None:
    before, after, button = _gtk_demo_snapshots()
    result = verify_action_result(
        before=before,
        after=after,
        target=button,
        action="invoke",
    )
    assert result["verified"] is True
    assert result["state_diff"]["text_value_changes"][0]["after"] == "Count: 1"


def test_verify_click_with_verify_label() -> None:
    before, after, button = _gtk_demo_snapshots()
    result = verify_action_result(
        before=before,
        after=after,
        target=button,
        action="invoke",
        verify_label="Count:",
    )
    assert result["verified"] is True
    assert result["state_diff"]["label_changes"][0]["before"] == "Count: 0"
    assert result["state_diff"]["label_changes"][0]["after"] == "Count: 1"


def test_verify_click_with_verify_selector() -> None:
    before, after, button = _gtk_demo_snapshots()
    result = verify_action_result(
        before=before,
        after=after,
        target=button,
        action="invoke",
        verify_selector='label[name="counter-label"]',
    )
    assert result["verified"] is True
    assert result["state_diff"]["selector_match"]["after"] == "Count: 1"


def test_verify_set_value_checks_expected_text() -> None:
    before_nodes = {
        "entry": _node("entry", role=ControlRole.INPUT, name="demo-entry", text_value=""),
    }
    after_nodes = {
        "entry": _node("entry", role=ControlRole.INPUT, name="demo-entry", text_value="hello"),
    }
    before = ControlSnapshot(backend="test", window_id=None, app_label="gtk_demo_app.py", nodes=before_nodes, root_ids=["entry"])
    after = ControlSnapshot(backend="test", window_id=None, app_label="gtk_demo_app.py", nodes=after_nodes, root_ids=["entry"])
    entry = before_nodes["entry"]

    result = verify_action_result(
        before=before,
        after=after,
        target=entry,
        action="set_value",
        expected_value="hello",
    )
    assert result["verified"] is True
    assert result["state_diff"]["text_value"]["after"] == "hello"


def test_snapshot_diff_alias_matches_diff_snapshots() -> None:
    before, after, _ = _gtk_demo_snapshots()
    assert snapshot_diff(before, after, scope_root_id="panel") == diff_snapshots(
        before, after, scope_root_id="panel"
    )


def test_collect_changed_nodes_flattens_diff() -> None:
    before, after, _ = _gtk_demo_snapshots()
    diff = diff_snapshots(before, after, scope_root_id="panel")
    changed = collect_changed_nodes(diff)
    assert len(changed) == 1
    assert changed[0]["kind"] == "text"
    assert changed[0]["after"] == "Count: 1"


def test_verify_detects_focus_change_without_value_change() -> None:
    before_nodes = {
        "panel": _node("panel", role=ControlRole.PANEL, children_ids=["entry"]),
        "entry": _node(
            "entry",
            role=ControlRole.INPUT,
            name="demo-entry",
            parent_id="panel",
            state={"focused": False},
        ),
    }
    after_nodes = {
        "panel": _node("panel", role=ControlRole.PANEL, children_ids=["entry"]),
        "entry": _node(
            "entry",
            role=ControlRole.INPUT,
            name="demo-entry",
            parent_id="panel",
            state={"focused": True},
        ),
    }
    before = ControlSnapshot(backend="test", window_id=None, app_label="demo", nodes=before_nodes, root_ids=["panel"])
    after = ControlSnapshot(backend="test", window_id=None, app_label="demo", nodes=after_nodes, root_ids=["panel"])
    entry = before_nodes["entry"]

    result = verify_action_result(
        before=before,
        after=after,
        target=entry,
        action="focus",
    )
    assert result["verified"] is True
    assert result["state_diff"]["focus_changes"][0]["after"] is True


def test_verify_fails_when_nothing_changes() -> None:
    before, after, button = _gtk_demo_snapshots()
    after.nodes["label"].text_value = "Count: 0"
    result = verify_action_result(
        before=before,
        after=after,
        target=button,
        action="invoke",
    )
    assert result["verified"] is False
    assert result["state_diff"] == {}
