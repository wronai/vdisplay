"""Deterministic normalization of VQL/IMGL sidecar elements.

The functions in this module are pure: they do not discover files, assess
freshness, select a target or authorize an action.  Those decisions belong to
the orchestrator consuming the normalized observation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def _element_sequence(payload: Any) -> tuple[list[Mapping[str, Any]], bool]:
    """Return ``(elements, fresh_bbox_semantics)`` from common payload shapes."""
    if isinstance(payload, Sequence) and not isinstance(payload, (str, bytes, bytearray)):
        return [item for item in payload if isinstance(item, Mapping)], False
    if not isinstance(payload, Mapping):
        return [], False

    ui_elements = payload.get("ui_elements")
    if isinstance(ui_elements, list) and ui_elements:
        return [item for item in ui_elements if isinstance(item, Mapping)], False
    elements = payload.get("elements")
    if isinstance(elements, list) and elements:
        return [item for item in elements if isinstance(item, Mapping)], True
    layers = payload.get("layers")
    if isinstance(layers, list) and layers:
        return [item for item in layers if isinstance(item, Mapping)], False

    metadata = payload.get("metadata")
    if isinstance(metadata, Mapping):
        render = metadata.get("render_intent")
        if isinstance(render, Mapping):
            nested, fresh = _element_sequence(render)
            if nested:
                return nested, fresh

    vql = payload.get("vql")
    if isinstance(vql, Mapping):
        program = vql.get("program", vql)
        nested, fresh = _element_sequence(program)
        if nested:
            return nested, fresh
    program = payload.get("program")
    if isinstance(program, Mapping):
        nested, fresh = _element_sequence(program)
        if nested:
            return nested, fresh
    return [], False


def _fresh_bounds(raw: Any) -> tuple[dict[str, Any], tuple[int, int, int, int]]:
    if isinstance(raw, Mapping):
        x = int(raw.get("x") or raw.get("left") or 0)
        y = int(raw.get("y") or raw.get("top") or 0)
        width = int(raw.get("w") or raw.get("width") or 0)
        height = int(raw.get("h") or raw.get("height") or 0)
        if not width and raw.get("right") is not None:
            width = max(0, int(raw.get("right") or 0) - x)
        if not height and raw.get("bottom") is not None:
            height = max(0, int(raw.get("bottom") or 0) - y)
    elif isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)) and len(raw) >= 4:
        x, y = int(raw[0]), int(raw[1])
        width = max(0, int(raw[2]) - x)
        height = max(0, int(raw[3]) - y)
    else:
        x = y = width = height = 0
    return (
        {
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "coordinate_space": "capture_frame_local",
        },
        (x, y, width, height),
    )


def _generic_bounds(raw: Any) -> tuple[Any, tuple[int, int, int, int]]:
    if isinstance(raw, Mapping):
        bounds = dict(raw)
        x = int(bounds.get("x") or bounds.get("left") or 0)
        y = int(bounds.get("y") or bounds.get("top") or 0)
        width = int(bounds.get("w") or bounds.get("width") or 0)
        height = int(bounds.get("h") or bounds.get("height") or 0)
        return bounds, (x, y, width, height)
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)):
        bounds = list(raw)
        if len(bounds) >= 4:
            return bounds, (
                int(bounds[0]),
                int(bounds[1]),
                max(0, int(bounds[2]) - int(bounds[0])),
                max(0, int(bounds[3]) - int(bounds[1])),
            )
        return bounds, (0, 0, 0, 0)
    return {}, (0, 0, 0, 0)


def _click_center(
    raw: Any,
    geometry: tuple[int, int, int, int],
    fallback_center: tuple[int, int],
) -> dict[str, int]:
    x, y, width, height = geometry
    fallback_x = x + width // 2 if width > 0 else fallback_center[0]
    fallback_y = y + height // 2 if height > 0 else fallback_center[1]
    if isinstance(raw, Mapping) and raw:
        return {
            "x": int(raw.get("x") or fallback_x),
            "y": int(raw.get("y") or fallback_y),
        }
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)) and len(raw) >= 2:
        return {"x": int(raw[0]), "y": int(raw[1])}
    return {"x": int(fallback_x), "y": int(fallback_y)}


def normalize_vql_ui_elements(
    payload: Any,
    *,
    fallback_center: tuple[int, int] = (0, 0),
) -> list[dict[str, Any]]:
    """Normalize common VQL/IMGL payload variants into stable UI elements."""
    elements, fresh = _element_sequence(payload)
    normalized: list[dict[str, Any]] = []
    for index, element in enumerate(elements):
        raw_bounds = element.get("bounds") or element.get("bbox") or {}
        bounds, geometry = (
            _fresh_bounds(raw_bounds) if fresh else _generic_bounds(raw_bounds)
        )
        center = _click_center(
            element.get("click_center") or element.get("center"),
            geometry,
            fallback_center,
        )
        element_id = element.get("id")
        role = element.get("role") or element.get("kind")
        label = (
            element.get("label") or element.get("text")
            if fresh
            else element.get("text") or element.get("label")
        )
        metadata_keys = ("color", "confidence", "location") if fresh else ("confidence", "location")
        normalized.append(
            {
                "id": (
                    str(element_id)
                    if element_id is not None
                    else f"elem-{index}" if fresh else None
                ),
                "role": role or ("unknown" if fresh else None),
                "label": label,
                "bounds": bounds,
                "click_center": center,
                "metadata": {
                    key: element.get(key)
                    for key in metadata_keys
                    if key in element
                },
            }
        )
    return normalized


__all__ = ["normalize_vql_ui_elements"]
