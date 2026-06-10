"""Verify-after-action: compare accessibility snapshots around control actions."""

from __future__ import annotations

from typing import Any

from .models import ControlNode, ControlRole, ControlSnapshot
from .selector import ControlSelector, find_matches, parse_selector, pick_match

_STATE_KEYS = ("focused", "expanded", "checked", "enabled", "visible")


def _node_key(node: ControlNode) -> tuple[str, str]:
    return (node.role.value, (node.name or "").strip().lower())


def _display_text(node: ControlNode) -> str | None:
    """Readable text for a control (AT-SPI often puts label copy in ``name``)."""
    if node.text_value is not None and node.text_value != "":
        return node.text_value
    if node.role == ControlRole.LABEL and node.name:
        return node.name
    return node.text_value


def _subtree_ids(snapshot: ControlSnapshot, root_id: str) -> set[str]:
    ids: set[str] = set()
    stack = [root_id]
    while stack:
        node_id = stack.pop()
        if node_id in ids or node_id not in snapshot.nodes:
            continue
        ids.add(node_id)
        stack.extend(snapshot.nodes[node_id].children_ids)
    return ids


def _scope_root_id(snapshot: ControlSnapshot, target: ControlNode) -> str:
    if target.parent_id and target.parent_id in snapshot.nodes:
        return target.parent_id
    return target.id


def _structural_key(snapshot: ControlSnapshot, node_id: str, scope_root_id: str) -> tuple[str, tuple[int, ...]]:
    node = snapshot.nodes[node_id]
    path: list[int] = []
    current = node_id
    while current != scope_root_id:
        current_node = snapshot.nodes.get(current)
        if current_node is None:
            break
        parent_id = current_node.parent_id
        if parent_id is None or parent_id not in snapshot.nodes:
            break
        parent = snapshot.nodes[parent_id]
        try:
            path.insert(0, parent.children_ids.index(current))
        except ValueError:
            break
        current = parent_id
    return (node.role.value, tuple(path))


def _nodes_by_match_key(
    snapshot: ControlSnapshot,
    node_ids: set[str],
    *,
    scope_root_id: str | None,
) -> dict[tuple[Any, ...], ControlNode]:
    keyed: dict[tuple[Any, ...], ControlNode] = {}
    for node_id in node_ids:
        node = snapshot.nodes.get(node_id)
        if node is None:
            continue
        if scope_root_id and scope_root_id in snapshot.nodes:
            key: tuple[Any, ...] = _structural_key(snapshot, node_id, scope_root_id)
        else:
            key = _node_key(node)
        keyed[key] = node
    return keyed


def diff_snapshots(
    before: ControlSnapshot,
    after: ControlSnapshot,
    *,
    scope_root_id: str | None = None,
) -> dict[str, Any]:
    """Diff two snapshots within a subtree, matching nodes structurally when scoped."""
    if scope_root_id is None:
        scope_ids = set(before.nodes) | set(after.nodes)
    else:
        scope_ids = _subtree_ids(before, scope_root_id) | _subtree_ids(after, scope_root_id)

    before_keyed = _nodes_by_match_key(before, scope_ids, scope_root_id=scope_root_id)
    after_keyed = _nodes_by_match_key(after, scope_ids, scope_root_id=scope_root_id)

    text_value_changes: list[dict[str, Any]] = []
    name_changes: list[dict[str, Any]] = []
    state_changes: list[dict[str, Any]] = []
    focus_changes: list[dict[str, Any]] = []
    added: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []

    for key, before_node in before_keyed.items():
        after_node = after_keyed.get(key)
        if after_node is None:
            removed.append({"role": before_node.role.value, "name": before_node.name})
            continue
        before_text = _display_text(before_node)
        after_text = _display_text(after_node)
        if before_text != after_text:
            text_value_changes.append(
                {
                    "role": before_node.role.value,
                    "name": before_node.name,
                    "before": before_text,
                    "after": after_text,
                }
            )
        if before_node.name != after_node.name:
            name_changes.append(
                {
                    "role": before_node.role.value,
                    "before": before_node.name,
                    "after": after_node.name,
                }
            )
        for state_key in _STATE_KEYS:
            before_val = before_node.state.get(state_key)
            after_val = after_node.state.get(state_key)
            if before_val is None and after_val is None:
                continue
            if before_val != after_val:
                change = {
                    "role": before_node.role.value,
                    "name": before_node.name,
                    "state": state_key,
                    "before": before_val,
                    "after": after_val,
                }
                state_changes.append(change)
                if state_key == "focused":
                    focus_changes.append(change)

    for key, after_node in after_keyed.items():
        if key not in before_keyed:
            added.append({"role": after_node.role.value, "name": after_node.name})

    return {
        "text_value_changes": text_value_changes,
        "name_changes": name_changes,
        "state_changes": state_changes,
        "focus_changes": focus_changes,
        "added_nodes": added,
        "removed_nodes": removed,
    }


def snapshot_diff(
    before: ControlSnapshot,
    after: ControlSnapshot,
    *,
    scope_root_id: str | None = None,
) -> dict[str, Any]:
    """Alias for :func:`diff_snapshots` — general before/after tree comparison."""
    return diff_snapshots(before, after, scope_root_id=scope_root_id)


def collect_changed_nodes(diff: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten a snapshot diff into a list of changed node summaries."""
    changed: list[dict[str, Any]] = []
    for item in diff.get("text_value_changes", []):
        changed.append({**item, "kind": "text"})
    for item in diff.get("focus_changes", []):
        changed.append({**item, "kind": "focus"})
    for item in diff.get("state_changes", []):
        if item.get("state") == "focused":
            continue
        changed.append({**item, "kind": "state"})
    for item in diff.get("name_changes", []):
        changed.append({**item, "kind": "name"})
    for item in diff.get("added_nodes", []):
        changed.append({**item, "kind": "added"})
    for item in diff.get("removed_nodes", []):
        changed.append({**item, "kind": "removed"})
    return changed


def _label_prefix_changes(
    before: ControlSnapshot,
    after: ControlSnapshot,
    *,
    prefix: str,
    scope_root_id: str | None = None,
) -> list[dict[str, Any]]:
    if scope_root_id is None:
        scope_ids = set(before.nodes) | set(after.nodes)
    else:
        scope_ids = _subtree_ids(before, scope_root_id) | _subtree_ids(after, scope_root_id)

    before_keyed = _nodes_by_match_key(before, scope_ids, scope_root_id=scope_root_id)
    after_keyed = _nodes_by_match_key(after, scope_ids, scope_root_id=scope_root_id)
    changes: list[dict[str, Any]] = []

    for key, before_node in before_keyed.items():
        after_node = after_keyed.get(key)
        if after_node is None:
            continue
        before_text = _display_text(before_node) or ""
        after_text = _display_text(after_node) or ""
        if not before_text.startswith(prefix) and not after_text.startswith(prefix):
            continue
        if before_text != after_text:
            changes.append(
                {
                    "role": before_node.role.value,
                    "name": before_node.name,
                    "before": before_text,
                    "after": after_text,
                }
            )
    return changes


def _label_prefix_changes_by_identity(
    before: ControlSnapshot,
    after: ControlSnapshot,
    *,
    prefix: str,
    scope_root_id: str,
) -> list[dict[str, Any]]:
    """Match label changes by (role, name) when structural keys shift between snapshots."""
    scope_before = _subtree_ids(before, scope_root_id)
    scope_after = _subtree_ids(after, scope_root_id)
    before_by_identity: dict[tuple[str, str | None], ControlNode] = {}
    for node_id in scope_before:
        node = before.nodes.get(node_id)
        if node is None:
            continue
        before_by_identity[(node.role.value, node.name)] = node

    changes: list[dict[str, Any]] = []
    for node_id in scope_after:
        after_node = after.nodes.get(node_id)
        if after_node is None:
            continue
        before_node = before_by_identity.get((after_node.role.value, after_node.name))
        if before_node is None:
            continue
        before_text = _display_text(before_node) or ""
        after_text = _display_text(after_node) or ""
        if not before_text.startswith(prefix) and not after_text.startswith(prefix):
            continue
        if before_text != after_text:
            changes.append(
                {
                    "role": before_node.role.value,
                    "name": before_node.name,
                    "before": before_text,
                    "after": after_text,
                }
            )
    return changes


def _selector_change(
    before: ControlSnapshot,
    after: ControlSnapshot,
    selector: ControlSelector,
) -> dict[str, Any] | None:
    before_node = pick_match(before.nodes, selector)
    after_node = pick_match(after.nodes, selector)
    if before_node is None or after_node is None:
        return None
    before_text = _display_text(before_node)
    after_text = _display_text(after_node)
    if before_text == after_text:
        return None
    return {
        "role": after_node.role.value,
        "name": after_node.name,
        "before": before_text,
        "after": after_text,
    }


def _handle_selector_verification(
    before: ControlSnapshot,
    after: ControlSnapshot,
    verify_selector: str | ControlSelector | None,
) -> dict[str, Any]:
    """Handle selector-based verification."""
    if verify_selector is None:
        return {}
    selector = verify_selector if isinstance(verify_selector, ControlSelector) else parse_selector(verify_selector)
    change = _selector_change(before, after, selector)
    if change is not None:
        return {"selector_match": change}
    return {}


def _handle_label_verification(
    before: ControlSnapshot,
    after: ControlSnapshot,
    verify_label: str | None,
    scope_root_id: str,
) -> dict[str, Any]:
    """Handle label prefix verification."""
    if not verify_label:
        return {}
    label_changes = _label_prefix_changes(before, after, prefix=verify_label, scope_root_id=scope_root_id)
    if not label_changes:
        label_changes = _label_prefix_changes_by_identity(
            before,
            after,
            prefix=verify_label,
            scope_root_id=scope_root_id,
        )
    if label_changes:
        return {"label_changes": label_changes}
    return {}


def _handle_set_value_verification(
    after: ControlSnapshot,
    target: ControlNode,
    scope_root: str,
    expected_value: str,
) -> dict[str, Any]:
    """Handle set_value action verification."""
    selector = ControlSelector(
        role=target.role.value,
        name=target.name,
        app=target.app_label,
        index=0,
    )
    after_node = pick_match(after.nodes, selector)
    if after_node is None and scope_root in after.nodes:
        after_scope = _subtree_ids(after, scope_root)
        after_inputs = [
            after.nodes[node_id]
            for node_id in after_scope
            if after.nodes[node_id].role == ControlRole.INPUT
        ]
        if after_inputs:
            after_node = after_inputs[0]
    if after_node is not None:
        return {
            "text_value": {
                "before": _display_text(target),
                "after": _display_text(after_node),
                "expected": expected_value,
            }
        }
    return {}


def _handle_focus_verification(diff: dict[str, Any]) -> dict[str, Any]:
    """Handle focus action verification."""
    if diff.get("focus_changes"):
        return {"focus_changes": diff["focus_changes"]}
    return {}


def _handle_invoke_verification(
    after: ControlSnapshot,
    target: ControlNode,
    diff: dict[str, Any],
    has_label_or_selector: bool,
) -> dict[str, Any]:
    """Handle invoke action verification."""
    state_diff: dict[str, Any] = {}
    if not has_label_or_selector and diff["text_value_changes"]:
        state_diff["text_value_changes"] = diff["text_value_changes"]
    if target.text_value is not None:
        after_target = after.nodes.get(target.id)
        if after_target is None:
            matches = find_matches(
                after.nodes,
                ControlSelector(role=target.role.value, name=target.name, app=target.app_label),
            )
            after_target = matches[0] if matches else None
        if after_target is not None and target.text_value != after_target.text_value:
            state_diff["target_text_value"] = {
                "before": target.text_value,
                "after": after_target.text_value,
            }
    return state_diff


def _add_diff_nodes(diff: dict[str, Any]) -> dict[str, Any]:
    """Add added/removed nodes from diff."""
    state_diff: dict[str, Any] = {}
    if diff.get("added_nodes"):
        state_diff["added_nodes"] = diff["added_nodes"]
    if diff.get("removed_nodes"):
        state_diff["removed_nodes"] = diff["removed_nodes"]
    return state_diff


def verify_action_result(
    *,
    before: ControlSnapshot,
    after: ControlSnapshot,
    target: ControlNode,
    action: str,
    expected_value: str | None = None,
    verify_label: str | None = None,
    verify_selector: str | ControlSelector | None = None,
) -> dict[str, Any]:
    """Build verification payload after a control action."""
    scope_root = _scope_root_id(before, target)
    diff = diff_snapshots(before, after, scope_root_id=scope_root)
    changed_nodes = collect_changed_nodes(diff)
    state_diff: dict[str, Any] = {}

    state_diff.update(_handle_selector_verification(before, after, verify_selector))
    state_diff.update(_handle_label_verification(before, after, verify_label, scope_root))

    if action == "set_value" and expected_value is not None:
        state_diff.update(_handle_set_value_verification(after, target, scope_root, expected_value))

    if action == "focus":
        state_diff.update(_handle_focus_verification(diff))

    if action == "invoke":
        state_diff.update(_handle_invoke_verification(after, target, diff, bool(verify_label or verify_selector)))

    state_diff.update(_add_diff_nodes(diff))

    if diff.get("state_changes"):
        state_diff["dom_state_changes"] = diff["state_changes"]
        state_diff["state_changes"] = diff["state_changes"]

    if not state_diff and changed_nodes:
        state_diff["changed_nodes"] = changed_nodes

    verified = _is_verified(action, state_diff, diff=diff, expected_value=expected_value)
    return {
        "verified": verified,
        "state_diff": state_diff,
        "changed_nodes": changed_nodes,
        "scope_root_id": scope_root,
    }


def _is_verified(
    action: str,
    state_diff: dict[str, Any],
    *,
    diff: dict[str, Any],
    expected_value: str | None,
) -> bool:
    if action == "set_value" and expected_value is not None:
        text_diff = state_diff.get("text_value") or {}
        return text_diff.get("after") == expected_value
        
    if action == "focus":
        focus_changes = state_diff.get("focus_changes") or diff.get("focus_changes") or []
        return any(item.get("after") is True for item in focus_changes)

    if state_diff.get("dom_state_changes"):
        return True

    keys = [
        "label_changes", "selector_match", "text_value_changes",
        "target_text_value", "focus_changes", "state_changes",
        "added_nodes", "removed_nodes", "changed_nodes",
    ]
    if any(state_diff.get(key) for key in keys):
        return True

    text_diff = state_diff.get("text_value")
    return bool(text_diff and text_diff.get("before") != text_diff.get("after"))
