"""Control-plane use-cases: list, find, click, focus, set-value."""

from __future__ import annotations

import base64
import os
import time
from typing import Any

from ...control.action_state import ControlActionPhase, ControlActionState, phase_from_payload
from ...control.base import ControlProvider
from ...control.engine import resolve_provider, resolve_provider_routing
from ...control.models import ControlNode
from ...control.policy import assess_control_capability, evaluate_provider_routing
from dataclasses import replace

from ...control.selector import ControlSelector, parse_selector, pick_match
from ...control.screenshot_verify import capture_control_screenshot
from ...control.verifier import VerifierPipeline, VerifyContext, verify_spec_from_flags
from ...control.gui_map import (
    GuiMapElement,
    load_gui_map,
    map_element_to_node,
    resolve_map_element,
    resolve_map_region,
    verify_hints_from_map_element,
)
from ...control.retry_policy import (
    RetryPolicy,
    apply_retry_decision,
    attach_retry_metadata,
    next_action,
    retry_enabled,
)
from ...control.verify_policy import aggregate_confidence, required_phases_from_context
from ...exceptions import VDisplayError


def _resolve_verify_mode(
    *,
    action: str,
    verify: bool,
    value: str | None,
    routing_mode: str,
    selected_provider: str | None = None,
) -> str:
    """Vision set-value must verify pasted/typed text, not anchor visibility."""
    if action == "set_value" and verify and value and selected_provider == "vision":
        return "ocr_contains"
    return routing_mode


def _control_settle_seconds(*, verify: bool, screenshot_verify: bool) -> float:
    """Pause after actuation so verify snapshots see settled UI (ms via env)."""
    if not verify and not screenshot_verify:
        return 0.0
    raw = os.environ.get("VDISPLAY_CONTROL_SETTLE_MS", "150")
    try:
        return max(0.0, int(raw)) / 1000.0
    except ValueError:
        return 0.15


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
        "vision_anchor",
        "vision_template",
        "vision_anchor_rel",
        "vision_target",
        "vision_min_confidence",
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
        vision_anchor=kwargs.get("vision_anchor"),
        vision_template=kwargs.get("vision_template"),
        vision_anchor_rel=kwargs.get("vision_anchor_rel"),
        vision_target=kwargs.get("vision_target"),
        vision_min_confidence=(
            float(kwargs["vision_min_confidence"])
            if kwargs.get("vision_min_confidence") is not None
            else None
        ),
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
            # With spatial anchor, --index disambiguates duplicate anchor labels (PR-24).
            pick_index = 0 if selector.vision_anchor_rel else selector.index
            index = max(0, pick_index)
            if index < len(matches):
                return matches[index]
    return pick_match(snapshot.nodes, selector)


def _load_map_pack(map_path: str | None):
    if not map_path:
        return None
    return load_gui_map(map_path)


def _resolve_map_target(map_path: str, map_target: str) -> GuiMapElement:
    pack = load_gui_map(map_path)
    return resolve_map_element(pack, map_target)


def _map_find_payload(map_path: str, map_scope: str | None = None) -> dict[str, Any]:
    pack = load_gui_map(map_path)
    element_ids: list[str]
    if map_scope:
        region = resolve_map_region(pack, map_scope)
        element_ids = list(region.elements)
    else:
        element_ids = list(pack.elements.keys())
    matches = [map_element_to_node(pack.elements[element_id]).to_dict() for element_id in element_ids if element_id in pack.elements]
    selected = matches[0] if matches else None
    return {
        "ok": True,
        "map": map_path,
        "scope": map_scope,
        "matches": matches,
        "selected": selected,
        "count": len(matches),
    }


def _execute_map_action(
    *,
    action: str,
    display: str | None,
    map_path: str,
    map_target: str,
    verify: bool,
    screenshot_verify: bool = False,
    value: str | None = None,
    verify_label: str | None = None,
    verify_selector: str | None = None,
    capture_fn: Any | None = None,
) -> dict[str, Any]:
    element = _resolve_map_target(map_path, map_target)
    target = map_element_to_node(element)
    hints = verify_hints_from_map_element(element)
    verify_label = verify_label or hints.get("verify_label")
    verify_selector = verify_selector or hints.get("verify_selector")
    from ...control.gui_map import resolve_map_verify_mode

    resolved_verify_mode = resolve_map_verify_mode(element, action=action, value=value)
    verify_semantic = verify and resolved_verify_mode in {
        "semantic",
        "hybrid",
        "dom",
        "ocr_contains",
        "anchor_visible",
    }
    effective_screenshot_verify = screenshot_verify or (
        verify and resolved_verify_mode in {"screenshot_diff", "hybrid"}
    )
    expected_verify_text = value or verify_label or element.identity.anchor_text

    from ...control.providers.vision import VisionStubProvider

    provider = VisionStubProvider(display=display)
    before_snapshot = provider.snapshot()
    before_png, screenshot_capture_meta = _capture_before_state(
        display=display,
        target=target,
        verify=verify,
        screenshot_verify=effective_screenshot_verify,
        verify_mode=resolved_verify_mode,
        capture_fn=capture_fn,
    )
    result = _perform_action(provider, action, target, value)
    settle_s = _control_settle_seconds(verify=verify, screenshot_verify=effective_screenshot_verify)
    if settle_s:
        time.sleep(settle_s)
    selector = ControlSelector(
        backend="vision",
        vision_anchor=element.identity.anchor_text,
        extra={"map_path": map_path, "map_target": map_target},
    )
    verification = VerifierPipeline().verify_after_action(
        VerifyContext(
            action_provider=provider,
            before_snapshot=before_snapshot,
            target=target,
            action=action,
            selector=selector,
            value=value,
            verify_label=verify_label or expected_verify_text,
            verify_selector=verify_selector,
            display=display,
            capture_fn=capture_fn,
            before_png=before_png,
            before_capture_meta=screenshot_capture_meta,
            verify_semantic=verify_semantic,
            verify_screenshot=effective_screenshot_verify,
            verify_mode=resolved_verify_mode,
            map_element=element,
        )
    )
    routing = evaluate_provider_routing(
        backend="vision",
        selector=selector,
        display=display,
        verify_semantic=verify,
        verify_screenshot=screenshot_verify,
    )
    return _build_action_payload(
        action=action,
        selector=selector,
        target=target,
        verify=verify,
        screenshot_verify=screenshot_verify,
        result={**result, "map_path": map_path, "map_target": map_target},
        routing=routing,
        verification=verification,
    )


def list_control_plugins() -> dict[str, Any]:
    from ...control.plugins import list_control_plugins as _list_plugins

    plugins = _list_plugins()
    return {"ok": True, "plugins": plugins, "total": len(plugins)}


def diagnose_control(
    *,
    display: str | None = None,
    backend: str = "auto",
    preview: bool = False,
    preview_output: str | None = None,
    preview_debug: bool = False,
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

    if preview and selector is not None:
        has_vision = bool(
            selector.vision_anchor
            or selector.vision_template
            or selector.vision_anchor_rel
            or backend == "vision"
        )
        if not has_vision:
            payload["preview"] = {
                "preview_available": False,
                "reason": "preview requires vision selector fields or --backend vision",
            }
        else:
            preview_backend = "vision" if backend == "auto" else backend
            try:
                find_payload = controls_find(
                    display=display,
                    backend=preview_backend,
                    preview=True,
                    preview_output=preview_output,
                    preview_debug=preview_debug,
                    **selector_kwargs,
                )
                payload["vision_find"] = {
                    "count": find_payload.get("count"),
                    "selected": find_payload.get("selected"),
                    "matches": find_payload.get("matches"),
                }
                if "preview" in find_payload:
                    payload["preview"] = find_payload["preview"]
            except VDisplayError as exc:
                payload["preview"] = {"preview_available": False, "reason": str(exc)}

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


def _attach_vision_preview(
    payload: dict[str, Any],
    *,
    provider: ControlProvider,
    nodes: list[ControlNode],
    selector: ControlSelector,
    preview: bool,
    preview_output: str | None,
    preview_debug: bool,
) -> dict[str, Any]:
    from ...control.providers.vision import VisionStubProvider
    from ...control.vision_preview import (
        build_vision_preview,
        preview_available,
        write_preview_png,
    )

    if not preview:
        return payload

    ready, reason = preview_available()
    if not ready:
        payload["preview"] = {"preview_available": False, "reason": reason}
        return payload

    if not isinstance(provider, VisionStubProvider):
        payload["preview"] = {
            "preview_available": False,
            "reason": "preview requires vision backend (use --backend vision)",
        }
        return payload

    capture = provider.last_capture()
    if capture is None:
        payload["preview"] = {"preview_available": False, "reason": "no vision screenshot captured"}
        return payload

    png, _meta = capture
    debug = provider.last_find_debug() if preview_debug else None
    preview_payload = build_vision_preview(png, nodes, selector=selector, debug=debug)
    if preview_output:
        overlay = base64.b64decode(preview_payload["preview_png_base64"])
        preview_payload["preview_path"] = write_preview_png(overlay, preview_output)
        payload.setdefault("artifacts", {})["preview"] = preview_payload["preview_path"]
    payload["preview"] = preview_payload
    return payload


def controls_find(
    *,
    display: str | None = None,
    backend: str = "auto",
    preview: bool = False,
    preview_output: str | None = None,
    preview_debug: bool = False,
    **selector_kwargs: Any,
) -> dict[str, Any]:
    map_path = selector_kwargs.get("map_path")
    map_scope = selector_kwargs.get("map_scope")
    if map_path and not any(
        selector_kwargs.get(key)
        for key in ("vision_anchor", "vision_template", "role", "name", "selector", "text", "text_contains")
    ):
        return _map_find_payload(map_path, map_scope)

    selector = _selector_from_kwargs(**selector_kwargs)
    session_id = selector_kwargs.get("session_id") or selector.session_id
    provider = resolve_provider(
        backend,
        **_provider_kwargs(display=display, session_id=session_id),
        selector=selector,
    )
    if preview_debug and hasattr(provider, "enable_preview_debug"):
        provider.enable_preview_debug(True)
    snapshot = provider.snapshot(
        app=selector.app or session_id,
        window_id=selector.window_id or session_id,
    )
    matches = provider.find(selector)
    if not matches:
        raise VDisplayError(f"no control matched selector: {selector}")
    picked = _resolve_target(provider, snapshot, selector)
    payload = {
        "ok": True,
        "matches": [node.to_dict() for node in matches[:20]],
        "selected": picked.to_dict() if picked else None,
        "count": len(matches),
    }
    return _attach_vision_preview(
        payload,
        provider=provider,
        nodes=matches,
        selector=selector,
        preview=preview,
        preview_output=preview_output,
        preview_debug=preview_debug,
    )


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
    if action == "set_value" and value is None:
        raise VDisplayError("set_value requires value")

    map_dispatch = {
        "invoke": ("invoke_map_node", "invoke"),
        "focus": ("focus_map_node", "focus"),
        "set_value": ("set_value_map_node", "set_value"),
    }
    if (target.state or {}).get("map"):
        map_method, fallback_method = map_dispatch.get(action, (None, None))
        if map_method and hasattr(provider, map_method):
            method = getattr(provider, map_method)
            return method(target) if action != "set_value" else method(target, value)

    standard_dispatch = {
        "invoke": lambda: provider.invoke(target.id),
        "focus": lambda: provider.focus(target.id),
        "set_value": lambda: provider.set_value(target.id, value),
    }
    if action in standard_dispatch:
        return standard_dispatch[action]()
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
    need_capture = screenshot_verify or (
        verify and verify_mode in {"hybrid", "screenshot_diff", "screenshot"}
    )
    if need_capture:
        return capture_control_screenshot(
            display=display,
            target=target,
            capture_fn=capture_fn,
        )
    return None, None


def _build_actuation_dict(result: dict[str, Any]) -> dict[str, Any]:
    return {
        key: result[key]
        for key in (
            "ok",
            "method",
            "reason",
            "x",
            "y",
            "local_x",
            "local_y",
            "backend",
            "value",
            "element_id",
        )
        if key in result
    }


def _build_map_block(result: dict[str, Any], selector_dict: dict[str, Any]) -> dict[str, Any] | None:
    map_path = result.get("map_path")
    map_target = result.get("map_target")
    if map_path or map_target:
        return {"path": map_path, "target": map_target}
    extra = selector_dict.get("extra") or {}
    if extra.get("map_path") or extra.get("map_target"):
        return {"path": extra.get("map_path"), "target": extra.get("map_target")}
    return None


def _build_verify_phases(verification_dict: dict[str, Any]) -> list[dict[str, Any]]:
    phases: list[dict[str, Any]] = []
    for phase_name in ("semantic", "visual", "ocr", "vision_llm", "layout", "session"):
        phase_payload = verification_dict.get(phase_name)
        if phase_payload:
            phases.append({"phase": phase_name, "payload": phase_payload})
    return phases


def _build_control_diagnostics(
    *,
    action: str,
    selector: Any,
    target: Any,
    verify: bool,
    screenshot_verify: bool,
    result: dict[str, Any],
    routing: Any,
    verification: Any,
    state: ControlActionState | None = None,
) -> dict[str, Any]:
    routing_dict = routing.to_dict() if hasattr(routing, "to_dict") else dict(routing or {})
    verification_dict = verification.to_dict() if hasattr(verification, "to_dict") else dict(verification or {})
    selector_dict = selector.to_dict() if hasattr(selector, "to_dict") else dict(getattr(selector, "__dict__", {}) or {})
    target_dict = target.to_dict() if hasattr(target, "to_dict") else dict(target or {})

    actuation = _build_actuation_dict(result)
    map_block = _build_map_block(result, selector_dict)
    verify_phases = _build_verify_phases(verification_dict)

    lifecycle = state.to_dict() if isinstance(state, ControlActionState) else None
    required = required_phases_from_context(
        action=action,
        verify=verify,
        screenshot_verify=screenshot_verify,
        verify_mode=str(verification_dict.get("mode") or routing_dict.get("verify_mode") or "semantic"),
        selector=selector if hasattr(selector, "to_dict") else None,
        map_element=result.get("map_element"),
    )
    confidence = verification_dict.get("confidence")
    if confidence is None:
        confidence = aggregate_confidence(verification_dict)

    control_block: dict[str, Any] = {
        "action": action,
        "selector": selector_dict,
        "target": target_dict,
        "map": map_block,
        "routing": routing_dict,
        "actuation": actuation,
        "verify": {
            "requested": verify,
            "screenshot_verify": screenshot_verify,
            "mode": verification_dict.get("mode"),
            "verified": verification_dict.get("verified"),
            "confidence": confidence,
            "reasons": list(verification_dict.get("reasons") or []),
            "phases": verify_phases,
            "required_phases": required,
        },
    }
    if lifecycle:
        control_block.update(
            {
                "action_id": lifecycle["action_id"],
                "phase": lifecycle["phase"],
                "attempt": lifecycle["attempt"],
                "lifecycle": lifecycle,
            }
        )
        if lifecycle.get("retry"):
            control_block["retry"] = lifecycle["retry"]

    return {"control": control_block}


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
    state: ControlActionState | None = None,
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
        artifact_paths: dict[str, str] = {}
        for side in ("before", "after", "diff"):
            block = screenshot_result.get(side)
            if isinstance(block, dict) and block.get("path"):
                artifact_paths[side] = str(block["path"])
        if artifact_paths:
            payload.setdefault("artifacts", {}).update(artifact_paths)
    if verify:
        payload["a11y_verified"] = a11y_verified
    if verify and verification.verified is False:
        payload["ok"] = False
        if action == "set_value":
            payload.setdefault("reason", "text_not_applied")
        else:
            payload.setdefault("reason", "verify_failed")
    payload["diagnostics"] = _build_control_diagnostics(
        action=action,
        selector=selector,
        target=target,
        verify=verify,
        screenshot_verify=screenshot_verify,
        result=payload,
        routing=routing,
        verification=verification,
        state=state,
    )
    if state is not None:
        payload["action_id"] = state.action_id
        payload["attempt"] = state.attempt
        payload["phase"] = state.phase.value
    return payload


def _execute_action_once(
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
    state: ControlActionState | None = None,
    **selector_kwargs: Any,
) -> dict[str, Any]:
    map_path = selector_kwargs.get("map_path")
    map_target = selector_kwargs.get("map_target")
    if map_path and map_target:
        return _execute_map_action(
            action=action,
            display=display,
            map_path=map_path,
            map_target=map_target,
            verify=verify,
            screenshot_verify=screenshot_verify,
            value=value,
            verify_label=verify_label,
            verify_selector=verify_selector,
            capture_fn=capture_fn,
        )

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

    settle_s = _control_settle_seconds(verify=verify, screenshot_verify=screenshot_verify)
    if settle_s:
        time.sleep(settle_s)

    effective_verify_mode = _resolve_verify_mode(
        action=action,
        verify=verify,
        value=value,
        routing_mode=routing.verify_mode,
        selected_provider=getattr(routing, "selected_provider", None),
    )

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
            verify_mode=effective_verify_mode,
            verify_provider=routing.verify_provider,
            spec=verify_spec_from_flags(
                verify_semantic=verify,
                verify_screenshot=screenshot_verify,
                verify_mode=effective_verify_mode,
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
        state=state,
    )


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
    if not retry_enabled(verify=verify, screenshot_verify=screenshot_verify):
        return _execute_action_once(
            action=action,
            display=display,
            backend=backend,
            verify=verify,
            screenshot_verify=screenshot_verify,
            value=value,
            verify_label=verify_label,
            verify_selector=verify_selector,
            capture_fn=capture_fn,
            **selector_kwargs,
        )

    policy = RetryPolicy.from_env()
    state = ControlActionState.new(action)
    current_backend = backend
    current_screenshot_verify = screenshot_verify
    kwargs = dict(selector_kwargs)
    kwargs.pop("backend", None)
    last_payload: dict[str, Any] | None = None

    for attempt in range(1, policy.max_attempts + 1):
        state = state.advance(ControlActionPhase.PLANNED, attempt=attempt)
        last_payload = _execute_action_once(
            action=action,
            display=display,
            backend=current_backend,
            verify=verify,
            screenshot_verify=current_screenshot_verify,
            value=value,
            verify_label=verify_label,
            verify_selector=verify_selector,
            capture_fn=capture_fn,
            state=state,
            **kwargs,
        )
        phase = ControlActionPhase.VERIFIED if last_payload.get("ok") else phase_from_payload(last_payload)
        verify_block = (last_payload.get("diagnostics") or {}).get("control", {}).get("verify", {})
        state = state.advance(phase, verify=verify_block if isinstance(verify_block, dict) else {})

        if last_payload.get("ok"):
            return last_payload

        decision = next_action(state, last_payload, policy=policy)
        if not decision.should_retry:
            state = state.advance(ControlActionPhase.RECOVERY_FAILED, retry={"reason": decision.reason})
            control = (last_payload.get("diagnostics") or {}).get("control") or {}
            last_payload.setdefault("diagnostics", {})["control"] = {
                **control,
                "phase": state.phase.value,
                "recovery_failed": decision.to_dict(),
            }
            last_payload["phase"] = state.phase.value
            return last_payload

        state = attach_retry_metadata(state, decision)
        current_backend, kwargs, current_screenshot_verify = apply_retry_decision(
            decision,
            backend=current_backend,
            selector_kwargs=kwargs,
            screenshot_verify=current_screenshot_verify,
        )
        if policy.delay_ms:
            time.sleep(policy.delay_ms / 1000.0)

    if last_payload is None:
        raise VDisplayError("control action produced no result")
    state = state.advance(
        ControlActionPhase.RECOVERY_FAILED,
        retry={"reason": "max_attempts_exhausted", "attempts": policy.max_attempts},
    )
    control = (last_payload.get("diagnostics") or {}).get("control") or {}
    last_payload.setdefault("diagnostics", {})["control"] = {
        **control,
        "phase": state.phase.value,
        "recovery_failed": {"reason": "max_attempts_exhausted", "attempts": policy.max_attempts},
    }
    last_payload["phase"] = state.phase.value
    return last_payload


def _build_tree(snapshot) -> list[dict[str, Any]]:
    def walk(node_id: str) -> dict[str, Any]:
        node = snapshot.nodes[node_id]
        payload = node.to_dict()
        payload["children"] = [walk(child_id) for child_id in node.children_ids if child_id in snapshot.nodes]
        return payload

    return [walk(root_id) for root_id in snapshot.root_ids if root_id in snapshot.nodes]