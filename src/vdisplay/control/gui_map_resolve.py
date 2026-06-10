"""GUI Map resolution functions — element/region lookup, node mapping, verify hints."""

from __future__ import annotations

from typing import Any

from ..exceptions import VDisplayError
from .gui_map import GuiMapBounds, GuiMapElement, GuiMapPack, GuiMapRegion
from .models import ControlNode, ControlRole


def resolve_map_element(pack: GuiMapPack, target_id: str) -> GuiMapElement:
    element = pack.elements.get(target_id)
    if element is None:
        raise VDisplayError(f"GUI map target not found: {target_id}")
    return element


def resolve_map_region(pack: GuiMapPack, scope_id: str) -> GuiMapRegion:
    region = pack.regions.get(scope_id)
    if region is None:
        raise VDisplayError(f"GUI map scope not found: {scope_id}")
    return region


def map_element_to_node(element: GuiMapElement) -> ControlNode:
    """Synthetic vision node using stored action bounds and capture metadata."""
    return ControlNode(
        id=f"map:{element.id}",
        backend="vision",
        role=ControlRole.INPUT if element.role in {"textbox", "input"} else ControlRole.UNKNOWN,
        name=element.identity.name or element.id,
        bounds=element.action_bounds.to_control_bounds(),
        state={
            "map": True,
            "map_element_id": element.id,
            "raw_bounds": element.raw_bounds.to_dict(),
            "action_bounds": element.action_bounds.to_dict(),
            "click_point": element.click_point.to_dict(),
            "anchor": element.identity.anchor_text or element.identity.name or element.id,
            "capture": dict(element.capture_meta),
            "verify_mode": element.verify_mode,
            "identity": element.identity.to_dict(),
            "region_id": element.region_id,
            "tile_fingerprint": element.tile_fingerprint,
        },
    )


def scoped_capture_region(pack: GuiMapPack, scope_id: str | None) -> tuple[int, int, int, int] | None:
    if not scope_id:
        return None
    region = resolve_map_region(pack, scope_id)
    bounds = region.scope_bounds
    return bounds.x, bounds.y, bounds.width, bounds.height


def verify_hints_from_map_element(element: GuiMapElement) -> dict[str, str | None]:
    hints: dict[str, str | None] = {"verify_mode": element.verify_mode}
    prefix = element.identity.name_prefix
    if prefix:
        hints["verify_label"] = prefix
    if element.identity.name:
        hints["verify_selector"] = f'label[name="{element.identity.name}"]'
    return hints


def resolve_map_verify_mode(
    element: GuiMapElement,
    *,
    action: str,
    value: str | None = None,
) -> str:
    """Map stored verify_mode to a vision-only pipeline mode (never semantic)."""
    raw = _normalize_verify_mode(element.verify_mode)
    if raw != "identity+region":
        return _direct_verify_mode(raw)
    return _identity_region_verify_mode(element, action=action, value=value)


def _normalize_verify_mode(mode: str | None) -> str:
    raw = (mode or "identity+region").strip().lower()
    if raw in {"semantic", "structure", "dom", "text", "hybrid"}:
        return "identity+region"
    return raw


def _direct_verify_mode(raw: str) -> str:
    if raw == "ocr":
        return "ocr_contains"
    if raw == "screenshot":
        return "screenshot_diff"
    return raw


def _identity_region_verify_mode(
    element: GuiMapElement,
    *,
    action: str,
    value: str | None,
) -> str:
    if action == "set_value" and value:
        return "ocr_contains"
    if element.identity.anchor_text:
        return "anchor_visible"
    label = element.identity.name_prefix or element.identity.name
    if label:
        return "ocr_contains"
    return "screenshot_diff"
