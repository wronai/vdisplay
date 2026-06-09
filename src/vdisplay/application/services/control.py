"""Control-plane use-cases: list, find, click, focus, set-value."""

from __future__ import annotations

from typing import Any

from ...control.base import ControlProvider
from ...control.engine import resolve_provider
from ...control.models import ControlNode
from ...control.policy import assess_control_capability
from ...control.selector import ControlSelector, parse_selector, pick_match
from ...control.screenshot_verify import capture_control_screenshot, verify_screenshot_pair
from ...control.verify import verify_action_result
from ...exceptions import VDisplayError


def _selector_from_kwargs(**kwargs: Any) -> ControlSelector:
    if kwargs.get("provider_ref"):
        return ControlSelector(
            accessibility_id=kwargs["provider_ref"],
            app=kwargs.get("app"),
            window_id=kwargs.get("window_id"),
            index=int(kwargs.get("index") or 0),
        )
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
        environment=kwargs.get("environment"),
        text=kwargs.get("text"),
        text_contains=kwargs.get("text_contains"),
        terminal_line=kwargs.get("terminal_line"),
        terminal_col=kwargs.get("terminal_col"),
        session_id=kwargs.get("session_id"),
        dom_css=kwargs.get("dom_css"),
        dom_xpath=kwargs.get("dom_xpath"),
    )


def _provider_kwargs(*, display: str | None, session_id: str | None) -> dict[str, Any]:
    payload: dict[str, Any] = {"display": display}
    if session_id:
        payload["session_id"] = session_id
    return payload


def _resolve_target(
    provider: ControlProvider,
    snapshot,
    selector: ControlSelector,
) -> ControlNode | None:
    find = getattr(provider, "find", None)
    if callable(find):
        matches = find(selector)
        if matches:
            index = max(0, selector.index)
            if index < len(matches):
                return matches[index]
    return pick_match(snapshot.nodes, selector)


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
    session_id: str | None = None,
) -> dict[str, Any]:
    provider = resolve_provider(
        backend,
        **_provider_kwargs(display=display, session_id=session_id),
    )
    snapshot = provider.snapshot(
        window_id=window_id or session_id,
        app=app or session_id,
        max_depth=max_depth,
    )
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
    session_id = selector_kwargs.get("session_id") or selector.session_id
    provider = resolve_provider(
        backend,
        **_provider_kwargs(display=display, session_id=session_id),
        selector=selector,
    )
    snapshot = provider.snapshot(
        app=selector.app or session_id,
        window_id=selector.window_id or session_id,
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
    screenshot_verify: bool = False,
    verify_label: str | None = None,
    verify_selector: str | None = None,
    **selector_kwargs: Any,
) -> dict[str, Any]:
    return _execute_action(
        action="invoke",
        display=display,
        backend=backend,
        verify=verify,
        screenshot_verify=screenshot_verify,
        verify_label=verify_label,
        verify_selector=verify_selector,
        **selector_kwargs,
    )


def control_focus(
    *,
    display: str | None = None,
    backend: str = "auto",
    verify: bool = False,
    screenshot_verify: bool = False,
    **selector_kwargs: Any,
) -> dict[str, Any]:
    return _execute_action(
        action="focus",
        display=display,
        backend=backend,
        verify=verify,
        screenshot_verify=screenshot_verify,
        **selector_kwargs,
    )


def control_set_value(
    *,
    value: str,
    display: str | None = None,
    backend: str = "auto",
    verify: bool = False,
    screenshot_verify: bool = False,
    verify_label: str | None = None,
    verify_selector: str | None = None,
    **selector_kwargs: Any,
) -> dict[str, Any]:
    return _execute_action(
        action="set_value",
        display=display,
        backend=backend,
        verify=verify,
        screenshot_verify=screenshot_verify,
        verify_label=verify_label,
        verify_selector=verify_selector,
        value=value,
        **selector_kwargs,
    )


def _perform_action(provider, action, target, value):
    if action == "invoke":
        return provider.invoke(target.id)
    if action == "focus":
        return provider.focus(target.id)
    if action == "set_value":
        if value is None:
            raise VDisplayError("set_value requires value")
        return provider.set_value(target.id, value)
    raise VDisplayError(f"unsupported control action: {action}")

def _verify_a11y(provider, selector, session_id, before_snapshot, target, action, value, verify_label, verify_selector):
    after_snapshot = provider.snapshot(
        app=selector.app or session_id,
        window_id=selector.window_id or session_id,
    )
    verification = verify_action_result(
        before=before_snapshot,
        after=after_snapshot,
        target=target,
        action=action,
        expected_value=value,
        verify_label=verify_label,
        verify_selector=verify_selector,
    )
    return verification["verified"], verification["state_diff"]

def _verify_screenshots(display, target, capture_fn, before_png, screenshot_capture_meta):
    after_png, after_meta = capture_control_screenshot(
        display=display,
        target=target,
        capture_fn=capture_fn,
    )
    compare_region = None
    if target.bounds is not None and target.bounds.width > 0 and target.bounds.height > 0:
        from ...control.screenshot_verify import _region_from_bounds
        compare_region = _region_from_bounds(target.bounds)
    screenshot_result = verify_screenshot_pair(
        before_png,
        after_png,
        region=compare_region,
        min_changed_ratio=0.00005,
    )
    screenshot_result["capture"] = {
        "before": screenshot_capture_meta,
        "after": after_meta,
    }
    return screenshot_result

def _aggregate_verified(verify, screenshot_verify, a11y_verified, screenshot_result):
    if verify and screenshot_verify:
        return bool(a11y_verified) and bool(screenshot_result and screenshot_result["verified"])
    if screenshot_verify:
        return bool(screenshot_result and screenshot_result["verified"])
    if verify:
        return a11y_verified
    return None

def _execute_action(
    *,
    action: str,
    display: str | None,
    backend: str,
    verify: bool,
    screenshot_verify: bool = False,
    value: str | None = None,
    verify_label: str | None = None,
    verify_selector: str | None = None,
    capture_fn: Any | None = None,
    **selector_kwargs: Any,
) -> dict[str, Any]:
    selector = _selector_from_kwargs(**selector_kwargs)
    session_id = selector_kwargs.get("session_id") or selector.session_id
    provider = resolve_provider(
        backend,
        **_provider_kwargs(display=display, session_id=session_id),
        selector=selector,
    )
    before_snapshot = provider.snapshot(
        app=selector.app or session_id,
        window_id=selector.window_id or session_id,
    )
    target = _resolve_target(provider, before_snapshot, selector)
    if target is None:
        raise VDisplayError(f"no control matched selector: {selector}")

    before_png: bytes | None = None
    screenshot_capture_meta: dict[str, Any] | None = None
    if screenshot_verify:
        before_png, screenshot_capture_meta = capture_control_screenshot(
            display=display,
            target=target,
            capture_fn=capture_fn,
        )

    result = _perform_action(provider, action, target, value)

    a11y_verified: bool | None = None
    state_diff: dict[str, Any] = {}
    if verify:
        a11y_verified, state_diff = _verify_a11y(
            provider, selector, session_id, before_snapshot, target, action, value, verify_label, verify_selector
        )

    screenshot_result: dict[str, Any] | None = None
    if screenshot_verify and before_png is not None:
        screenshot_result = _verify_screenshots(
            display, target, capture_fn, before_png, screenshot_capture_meta
        )

    verified = _aggregate_verified(verify, screenshot_verify, a11y_verified, screenshot_result)

    payload = {
        **result,
        "action": action,
        "selector": selector.__dict__,
        "target": target.to_dict(),
        "verify": verify,
        "screenshot_verify": screenshot_verify,
        "verified": verified,
        "state_diff": state_diff,
    }
    if screenshot_result is not None:
        payload["screenshot_diff"] = screenshot_result
    if verify:
        payload["a11y_verified"] = a11y_verified
    return payload


def _build_tree(snapshot) -> list[dict[str, Any]]:
    def walk(node_id: str) -> dict[str, Any]:
        node = snapshot.nodes[node_id]
        payload = node.to_dict()
        payload["children"] = [walk(child_id) for child_id in node.children_ids if child_id in snapshot.nodes]
        return payload

    return [walk(root_id) for root_id in snapshot.root_ids if root_id in snapshot.nodes]
