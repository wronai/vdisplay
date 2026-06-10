"""Verify phase selection and confidence aggregation (PR-D)."""

from __future__ import annotations

from typing import Any

from .models import ControlNode
from .selector import ControlSelector


def _get_base_phases(verify: bool, screenshot_verify: bool, mode: str) -> list[str]:
    phases: list[str] = []
    if verify and mode in {"semantic", "hybrid", "dom", "anchor_visible"}:
        phases.append("semantic")
    if screenshot_verify or mode in {"screenshot_diff", "hybrid", "screenshot"}:
        phases.append("visual")
    if verify and mode in {"ocr_contains", "hybrid", "identity+region"}:
        phases.append("ocr")
    return phases


def required_phases(
    *,
    action: str,
    verify: bool,
    screenshot_verify: bool,
    verify_mode: str,
    map_element: Any | None = None,
    selector: ControlSelector | None = None,
) -> list[str]:
    if not verify and not screenshot_verify:
        return []

    mode = (verify_mode or "semantic").lower()
    phases = _get_base_phases(verify, screenshot_verify, mode)

    if map_element is not None:
        phases.append("layout")
    if selector is not None and selector.session_id and mode in {"dom", "hybrid"}:
        phases.append("session")

    if not phases and verify:
        phases.append("semantic")
    return _dedupe(phases)


def aggregate_confidence(phase_results: dict[str, Any]) -> float:
    scores: list[float] = []
    for key in ("semantic", "visual", "ocr", "vision_llm", "layout", "session"):
        block = phase_results.get(key)
        if not isinstance(block, dict):
            continue
        if block.get("verified") is True:
            scores.append(float(block.get("confidence") or 1.0))
        elif block.get("verified") is False:
            scores.append(float(block.get("confidence") or 0.0))
    if not scores:
        verified = phase_results.get("verified")
        if verified is True:
            return float(phase_results.get("confidence") or 1.0)
        if verified is False:
            return float(phase_results.get("confidence") or 0.0)
        return 0.0
    return round(sum(scores) / len(scores), 4)


def required_phases_from_context(
    *,
    action: str,
    verify: bool,
    screenshot_verify: bool,
    verify_mode: str,
    target: ControlNode | None = None,
    selector: ControlSelector | None = None,
    map_element: Any | None = None,
) -> list[str]:
    return required_phases(
        action=action,
        verify=verify,
        screenshot_verify=screenshot_verify,
        verify_mode=verify_mode,
        map_element=map_element,
        selector=selector,
    )


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered