"""Extract normalized control diagnostics from command results."""

from __future__ import annotations

from typing import Any

from .commands import CommandResult


def extract_diagnostics(result: CommandResult) -> dict[str, Any]:
    diagnostics: dict[str, Any] = dict(result.diagnostics or {})
    data = result.data or {}
    embedded = data.get("diagnostics")
    if isinstance(embedded, dict):
        diagnostics = _merge_diagnostics(embedded, diagnostics)

    control: dict[str, Any] = {}
    if isinstance(diagnostics.get("control"), dict):
        control = dict(diagnostics["control"])

    if isinstance(data.get("control"), dict):
        control = _merge_diagnostics({"control": control}, {"control": data["control"]}).get("control", control)

    legacy = _legacy_control_diagnostics(data)
    if legacy.get("routing"):
        control.setdefault("routing", legacy["routing"])
    if legacy.get("verify"):
        control["verify"] = _merge_diagnostics(
            control.get("verify") if isinstance(control.get("verify"), dict) else {},
            legacy["verify"],
        )

    synthesized = _synthesize_control_block(data)
    if synthesized:
        control = _merge_diagnostics({"control": control}, {"control": synthesized}).get("control", control)

    if control:
        diagnostics["control"] = control
        if isinstance(control.get("routing"), dict):
            diagnostics.setdefault("routing", control["routing"])
        if isinstance(control.get("verify"), dict):
            diagnostics.setdefault("verify", control["verify"])

    return diagnostics


def _add_base_fields(data: dict[str, Any], block: dict[str, Any]) -> None:
    action = data.get("action")
    if isinstance(action, str) and action:
        block["action"] = action
    for key in ("action_id", "phase", "attempt", "target", "selector"):
        if key in data and data[key] is not None:
            block[key] = data[key]


def _add_map_block(data: dict[str, Any], block: dict[str, Any]) -> None:
    if data.get("map_path") or data.get("map_target"):
        block["map"] = {
            "path": data.get("map_path"),
            "target": data.get("map_target"),
        }


def _add_routing_block(data: dict[str, Any], block: dict[str, Any]) -> None:
    routing = data.get("routing")
    if isinstance(routing, dict):
        block["routing"] = routing
    control_probe = data.get("control")
    if isinstance(control_probe, dict) and control_probe.get("backend"):
        block.setdefault("routing", {})
        if isinstance(block["routing"], dict):
            block["routing"].setdefault("selected_provider", control_probe["backend"])


def _add_verification_block(data: dict[str, Any], block: dict[str, Any]) -> None:
    verification = data.get("verification")
    if isinstance(verification, dict):
        block["verify"] = _verification_to_verify_block(verification)
    else:
        verify: dict[str, Any] = {}
        for key in ("verified", "verify_mode", "verify_confidence", "verify_reasons"):
            if key in data:
                verify[key] = data[key]
        if verify:
            block["verify"] = verify


def _add_actuation_block(data: dict[str, Any], block: dict[str, Any]) -> None:
    actuation = {
        key: data[key]
        for key in ("method", "reason", "backend", "x", "y", "local_x", "local_y", "value", "element_id")
        if key in data
    }
    action = data.get("action")
    if "ok" in data and (
        actuation
        or (isinstance(action, str) and action in {"invoke", "click", "focus", "set_value", "press"})
    ):
        actuation["ok"] = data["ok"]
    if actuation:
        block["actuation"] = actuation


def _add_lifecycle_blocks(data: dict[str, Any], block: dict[str, Any]) -> None:
    for key in ("retry", "recovery_failed", "lifecycle"):
        if isinstance(data.get(key), dict):
            block[key] = data[key]


def _synthesize_control_block(data: dict[str, Any]) -> dict[str, Any]:
    """Build diagnostics.control from flat handler payloads (mocks, legacy paths)."""
    block: dict[str, Any] = {}
    _add_base_fields(data, block)
    _add_map_block(data, block)
    _add_routing_block(data, block)
    _add_verification_block(data, block)
    _add_actuation_block(data, block)
    _add_lifecycle_blocks(data, block)
    return block


def _verification_to_verify_block(verification: dict[str, Any]) -> dict[str, Any]:
    block = dict(verification)
    phases: list[dict[str, Any]] = []
    for phase_name in ("semantic", "visual", "ocr", "vision_llm", "layout", "session"):
        phase_payload = verification.get(phase_name)
        if isinstance(phase_payload, dict):
            phases.append({"phase": phase_name, "payload": phase_payload})
    if phases:
        block["phases"] = phases
    return block


def _merge_diagnostics(primary: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = dict(primary)
    for key, value in overlay.items():
        if key not in merged:
            merged[key] = value
        elif isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    return merged


def _legacy_control_diagnostics(data: dict[str, Any]) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {}
    routing = data.get("routing")
    if isinstance(routing, dict):
        diagnostics["routing"] = {
            "selected_provider": routing.get("selected_provider"),
            "requested_backend": routing.get("requested_backend"),
            "verify_provider": routing.get("verify_provider"),
            "verify_mode": routing.get("verify_mode"),
            "application_profile": routing.get("application_profile"),
            "why_selected": routing.get("why_selected"),
            "why_not_selected": routing.get("why_not_selected"),
        }
    verify: dict[str, Any] = {}
    for key in ("verified", "verify_mode", "verify_confidence", "verify_reasons", "method", "reason"):
        if key in data:
            verify[key] = data[key]
    if verify:
        diagnostics["verify"] = verify
    return diagnostics
