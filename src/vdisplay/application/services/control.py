"""Control-plane use-cases: list, find, click, focus, set-value."""

from __future__ import annotations

from typing import Any

from ...control.engine import resolve_provider
from ...control.policy import assess_control_capability
from ...control.selector import ControlSelector, parse_selector, pick_match
from ...exceptions import VDisplayError


def _selector_from_kwargs(**kwargs: Any) -> ControlSelector:
    if kwargs.get("selector"):
        raw = kwargs["selector"]
        if isinstance(raw, str):
            return parse_selector(raw)
        if isinstance(raw, dict):
            return ControlSelector.from_dict(raw)
    return ControlSelector(
        role=kwargs.get("role"),
        name=kwargs.get("name"),
        name_contains=kwargs.get("name_contains"),
        app=kwargs.get("app"),
        window_id=kwargs.get("window_id"),
        window_title=kwargs.get("window_title"),
        index=int(kwargs.get("index") or 0),
    )


def diagnose_control(*, display: str | None = None) -> dict[str, Any]:
    contract = assess_control_capability(display=display)
    return {"ok": True, "control": contract.to_dict()}


def controls_list(
    *,
    display: str | None = None,
    window_id: str | None = None,
    app: str | None = None,
    backend: str = "auto",
    max_depth: int = 8,
    format: str = "flat",
) -> dict[str, Any]:
    provider = resolve_provider(backend, display=display)
    snapshot = provider.snapshot(window_id=window_id, app=app, max_depth=max_depth)
    payload = snapshot.to_dict()
    payload["ok"] = True
    if format == "tree":
        payload["tree"] = _build_tree(snapshot)
    return payload


def controls_find(
    *,
    display: str | None = None,
    backend: str = "auto",
    **selector_kwargs: Any,
) -> dict[str, Any]:
    selector = _selector_from_kwargs(**selector_kwargs)
    provider = resolve_provider(backend, display=display)
    snapshot = provider.snapshot(
        app=selector.app,
        window_id=selector.window_id,
    )
    matches = provider.find(selector)
    if not matches:
        raise VDisplayError(f"no control matched selector: {selector}")
    picked = pick_match(snapshot.nodes, selector)
    return {
        "ok": True,
        "matches": [node.to_dict() for node in matches[:20]],
        "selected": picked.to_dict() if picked else None,
        "count": len(matches),
    }


def control_click(
    *,
    display: str | None = None,
    backend: str = "auto",
    verify: bool = False,
    **selector_kwargs: Any,
) -> dict[str, Any]:
    return _execute_action(
        action="invoke",
        display=display,
        backend=backend,
        verify=verify,
        **selector_kwargs,
    )


def control_focus(
    *,
    display: str | None = None,
    backend: str = "auto",
    **selector_kwargs: Any,
) -> dict[str, Any]:
    return _execute_action(
        action="focus",
        display=display,
        backend=backend,
        verify=False,
        **selector_kwargs,
    )


def control_set_value(
    *,
    value: str,
    display: str | None = None,
    backend: str = "auto",
    verify: bool = False,
    **selector_kwargs: Any,
) -> dict[str, Any]:
    return _execute_action(
        action="set_value",
        display=display,
        backend=backend,
        verify=verify,
        value=value,
        **selector_kwargs,
    )


def _execute_action(
    *,
    action: str,
    display: str | None,
    backend: str,
    verify: bool,
    value: str | None = None,
    **selector_kwargs: Any,
) -> dict[str, Any]:
    selector = _selector_from_kwargs(**selector_kwargs)
    provider = resolve_provider(backend, display=display)
    snapshot = provider.snapshot(app=selector.app, window_id=selector.window_id)
    target = pick_match(snapshot.nodes, selector)
    if target is None:
        raise VDisplayError(f"no control matched selector: {selector}")

    before = target.text_value
    if action == "invoke":
        result = provider.invoke(target.id)
    elif action == "focus":
        result = provider.focus(target.id)
    elif action == "set_value":
        if value is None:
            raise VDisplayError("set_value requires value")
        result = provider.set_value(target.id, value)
    else:
        raise VDisplayError(f"unsupported control action: {action}")

    after_value = before
    state_diff: dict[str, Any] = {}
    if verify:
        refreshed = provider.snapshot(app=selector.app, window_id=selector.window_id)
        refreshed_node = refreshed.nodes.get(target.id)
        if refreshed_node is not None:
            after_value = refreshed_node.text_value
            if before != after_value:
                state_diff["text_value"] = {"before": before, "after": after_value}

    return {
        **result,
        "action": action,
        "selector": selector.__dict__,
        "target": target.to_dict(),
        "verify": verify,
        "state_diff": state_diff,
    }


def _build_tree(snapshot) -> list[dict[str, Any]]:
    def walk(node_id: str) -> dict[str, Any]:
        node = snapshot.nodes[node_id]
        payload = node.to_dict()
        payload["children"] = [walk(child_id) for child_id in node.children_ids if child_id in snapshot.nodes]
        return payload

    return [walk(root_id) for root_id in snapshot.root_ids if root_id in snapshot.nodes]
