"""Control-plane use-cases: list, find, click, focus, set-value."""

from __future__ import annotations

from typing import Any

from ...control.base import ControlProvider
from ...control.engine import resolve_provider, resolve_provider_routing
from ...control.models import ControlNode
from ...control.policy import assess_control_capability, evaluate_provider_routing
from dataclasses import replace

from ...control.selector import ControlSelector, parse_selector, pick_match
from ...control.screenshot_verify import capture_control_screenshot
from ...control.verifier import VerifierPipeline, VerifyContext, verify_spec_from_flags
from ...exceptions import VDisplayError


def _apply_selector_overrides(selector: ControlSelector, **kwargs: Any) -> ControlSelector:
    overrides = {key: value for key, value in kwargs.items() if key != "selector"}
    updates: dict[str, Any] = {}
    for key in (
        "session_id",
        "backend",
        "app",
        "window_id",
        "window_title",
        "environment",
        "role",
        "name",
        "name_contains",
        "text",
        "text_contains",
        "terminal_line",
        "terminal_col",
    ):
        value = overrides.get(key)
        if value is not None and value != "":
            updates[key] = value
    if "index" in overrides and overrides.get("index") is not None:
        updates["index"] = int(overrides["index"])
    return replace(selector, **updates) if updates else selector


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
        overrides = {key: value for key, value in kwargs.items() if key != "selector"}
        if isinstance(raw, str):
            return _apply_selector_overrides(parse_selector(raw), **overrides)
        if isinstance(raw, dict):
            return _apply_selector_overrides(ControlSelector.from_dict(raw), **overrides)
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
        backend=kwargs.get("backend"),
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


def list_control_plugins() -> dict[str, Any]:
    from ...control.plugins import list_control_plugins as _list_plugins

    plugins = _list_plugins()
    return {"ok": True, "plugins": plugins, "total": len(plugins)}


def diagnose_control(
    *,
    display: str | None = None,
    backend: str = "auto",
    **selector_kwargs: Any,
) -> dict[str, Any]:
    contract = assess_control_capability(display=display)
    selector = _selector_from_kwargs(**selector_kwargs) if selector_kwargs else None
    session_id = selector_kwargs.get("session_id")
    routing = evaluate_provider_routing(
        backend=backend,
        selector=selector,
        session_id=session_id,
        display=display,
    )
    from ...control.descriptors import extension_catalog
    from ...control.profile_inference import infer_application_profile
    from ...control.routing_semantics import build_routing_semantics

    inferred = infer_application_profile(selector, session_id=session_id)
    semantics = build_routing_semantics(selector=selector, session_id=session_id, display=display)
    from ...control.browser_engine import resolve_session_browser_engine

    browser_engine = resolve_session_browser_engine(session_id)

    payload: dict[str, Any] = {
        "ok": True,
        "control": contract.to_dict(),
        "routing": routing.to_dict(),
        "routing_semantics": semantics.to_dict(),
        "extensions": extension_catalog(),
        "application_profile": inferred.to_dict() if inferred else None,
    }
    if browser_engine is not None:
        payload["browser_engine"] = browser_engine.value
    if session_id:
        payload["session_id"] = session_id
    return payload


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

def _capture_before_state(
    *,
    display: str | None,
    target: Any,
    verify: bool,
    screenshot_verify: bool,
    verify_mode: str | None,
    capture_fn: Any | None,
) -> tuple[bytes | None, dict[str, Any] | None]:
    need_capture = screenshot_verify or (verify and verify_mode == "hybrid")
    if need_capture:
        return capture_control_screenshot(
            display=display,
            target=target,
            capture_fn=capture_fn,
        )
    return None, None


def _build_action_payload(
    *,
    action: str,
    selector: Any,
    target: Any,
    verify: bool,
    screenshot_verify: bool,
    result: dict[str, Any],
    routing: Any,
    verification: Any,
) -> dict[str, Any]:
    state_diff = (verification.semantic or {}).get("state_diff") or {}
    screenshot_result = verification.visual
    a11y_verified = verification.semantic.get("verified") if verification.semantic else None

    payload = {
        **result,
        "action": action,
        "selector": selector.__dict__,
        "target": target.to_dict(),
        "verify": verify,
        "screenshot_verify": screenshot_verify,
        "verified": verification.verified,
        "verify_confidence": verification.confidence,
        "verify_mode": verification.mode,
        "verify_reasons": verification.reasons,
        "state_diff": state_diff,
        "routing": routing.to_dict(),
        "verification": verification.to_dict(),
    }
    if screenshot_result is not None:
        payload["screenshot_diff"] = screenshot_result
    if verify:
        payload["a11y_verified"] = a11y_verified
    return payload


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
    provider, routing = resolve_provider_routing(
        backend,
        **_provider_kwargs(display=display, session_id=session_id),
        selector=selector,
        verify_semantic=verify,
        verify_screenshot=screenshot_verify,
    )
    before_snapshot = provider.snapshot(
        app=selector.app or session_id,
        window_id=selector.window_id or session_id,
    )
    target = _resolve_target(provider, before_snapshot, selector)
    if target is None:
        raise VDisplayError(f"no control matched selector: {selector}")

    before_png, screenshot_capture_meta = _capture_before_state(
        display=display,
        target=target,
        verify=verify,
        screenshot_verify=screenshot_verify,
        verify_mode=routing.verify_mode,
        capture_fn=capture_fn,
    )

    result = _perform_action(provider, action, target, value)

    verification = VerifierPipeline().verify_after_action(
        VerifyContext(
            action_provider=provider,
            before_snapshot=before_snapshot,
            target=target,
            action=action,
            selector=selector,
            session_id=session_id,
            value=value,
            verify_label=verify_label,
            verify_selector=verify_selector,
            display=display,
            capture_fn=capture_fn,
            before_png=before_png,
            before_capture_meta=screenshot_capture_meta,
            verify_semantic=verify,
            verify_screenshot=screenshot_verify,
            verify_mode=routing.verify_mode or "semantic",
            verify_provider=routing.verify_provider,
            spec=verify_spec_from_flags(
                verify_semantic=verify,
                verify_screenshot=screenshot_verify,
                verify_mode=routing.verify_mode or "semantic",
                verify_label=verify_label,
                expected_text=value,
            ),
        )
    )

    return _build_action_payload(
        action=action,
        selector=selector,
        target=target,
        verify=verify,
        screenshot_verify=screenshot_verify,
        result=result,
        routing=routing,
        verification=verification,
    )


def _build_tree(snapshot) -> list[dict[str, Any]]:
    def walk(node_id: str) -> dict[str, Any]:
        node = snapshot.nodes[node_id]
        payload = node.to_dict()
        payload["children"] = [walk(child_id) for child_id in node.children_ids if child_id in snapshot.nodes]
        return payload

    return [walk(root_id) for root_id in snapshot.root_ids if root_id in snapshot.nodes]
