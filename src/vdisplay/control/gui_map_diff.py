"""GUI Map Pack drift detection and refresh (PR-27)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Literal

from .action_bounds import action_bounds_for_vision, click_point_for_vision
from .gui_map import (
    GuiMapBounds,
    GuiMapElement,
    GuiMapPack,
    GuiMapPoint,
    GuiMapRegion,
    element_from_ocr_box,
    tile_fingerprint,
)
from .vision_ocr import OcrTextBox

DriftKind = Literal["ok", "fingerprint", "bounds", "missing", "anchor"]


@dataclass
class ElementDrift:
    element_id: str
    status: DriftKind
    message: str
    stored_bounds: dict[str, int] | None = None
    live_bounds: dict[str, int] | None = None
    stored_fingerprint: str | None = None
    live_fingerprint: str | None = None
    delta_px: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "element_id": self.element_id,
            "status": self.status,
            "message": self.message,
            "stored_bounds": self.stored_bounds,
            "live_bounds": self.live_bounds,
            "stored_fingerprint": self.stored_fingerprint,
            "live_fingerprint": self.live_fingerprint,
            "delta_px": self.delta_px,
        }


@dataclass
class RegionDrift:
    region_id: str
    status: DriftKind
    message: str
    stored_fingerprint: str | None = None
    live_fingerprint: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "region_id": self.region_id,
            "status": self.status,
            "message": self.message,
            "stored_fingerprint": self.stored_fingerprint,
            "live_fingerprint": self.live_fingerprint,
        }


@dataclass
class GuiMapDiff:
    ok: bool
    drifted: bool
    elements: list[ElementDrift] = field(default_factory=list)
    regions: list[RegionDrift] = field(default_factory=list)
    new_ocr_labels: list[str] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)
    recommendation: str = "stable"
    actionable: bool = False
    key_targets: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "drifted": self.drifted,
            "recommendation": self.recommendation,
            "actionable": self.actionable,
            "key_targets": dict(self.key_targets),
            "summary": dict(self.summary),
            "elements": [item.to_dict() for item in self.elements],
            "regions": [item.to_dict() for item in self.regions],
            "new_ocr_labels": list(self.new_ocr_labels[:50]),
        }


def _center(bounds: GuiMapBounds) -> tuple[float, float]:
    cx, cy = bounds.center
    return float(cx), float(cy)


def _distance(a: GuiMapBounds, b: GuiMapBounds) -> float:
    ax, ay = _center(a)
    bx, by = _center(b)
    return math.hypot(ax - bx, ay - by)


def _box_to_bounds(box: OcrTextBox) -> GuiMapBounds:
    return GuiMapBounds.from_control_bounds(box.bounds)


def _normalize_label(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _labels_match(stored: str | None, live: str | None) -> bool:
    if not stored or not live:
        return False
    a = _normalize_label(stored)
    b = _normalize_label(live)
    return a == b or a in b or b in a


def _boxes_in_scope(boxes: list[OcrTextBox], scope: GuiMapBounds | None) -> list[OcrTextBox]:
    if scope is None:
        return boxes
    kept: list[OcrTextBox] = []
    for box in boxes:
        bounds = _box_to_bounds(box)
        cx, cy = bounds.center
        if (
            scope.x <= cx <= scope.x + scope.width
            and scope.y <= cy <= scope.y + scope.height
        ):
            kept.append(box)
    return kept


def match_ocr_box_for_element(
    element: GuiMapElement,
    boxes: list[OcrTextBox],
    *,
    max_distance_px: float = 240.0,
) -> OcrTextBox | None:
    """Find live OCR box for a stored element by anchor/name, preferring nearest center."""
    anchor = element.identity.anchor_text or element.identity.name
    candidates = boxes
    if anchor:
        labeled = [box for box in boxes if _labels_match(anchor, box.text)]
        if labeled:
            candidates = labeled
    if not candidates:
        return None
    stored = element.raw_bounds
    ranked = sorted(candidates, key=lambda box: _distance(stored, _box_to_bounds(box)))
    best = ranked[0]
    if _distance(stored, _box_to_bounds(best)) > max_distance_px and anchor:
        return None
    return best


def assess_map_drift(
    diff: GuiMapDiff,
    *,
    refresh_ratio: float = 0.25,
    key_target_ids: tuple[str, ...] = ("chat", "message", "ask_anything"),
) -> tuple[str, bool, dict[str, str]]:
    """Return (recommendation, actionable, key_target_statuses)."""
    total = sum(diff.summary.values())
    if total == 0:
        return "stable", False, {}

    missing = diff.summary.get("missing", 0)
    bounds = diff.summary.get("bounds", 0)
    fingerprint = diff.summary.get("fingerprint", 0)
    problematic = missing + bounds
    ratio = problematic / total if total else 0.0
    region_drift = any(item.status != "ok" for item in diff.regions)

    key_targets = {
        item.element_id: item.status
        for item in diff.elements
        if item.element_id in key_target_ids
    }
    key_bad = any(status in {"missing", "bounds"} for status in key_targets.values())

    if key_bad or ratio >= refresh_ratio or missing > max(3, total // 3):
        recommendation = "refresh_required"
        actionable = True
    elif problematic > 0 or region_drift:
        recommendation = "refresh_recommended"
        actionable = True
    elif fingerprint > 0:
        recommendation = "stable_with_cosmetic_drift"
        actionable = False
    else:
        recommendation = "stable"
        actionable = False
    return recommendation, actionable, key_targets


def diff_gui_map(
    pack: GuiMapPack,
    png: bytes,
    capture_meta: dict[str, Any],
    *,
    scope_id: str | None = None,
    min_confidence: float = 0.5,
    bounds_tolerance_px: float = 12.0,
) -> GuiMapDiff:
    """Compare stored map against a fresh capture + OCR."""
    from .vision_ocr import ocr_png

    boxes = [box for box in ocr_png(png) if box.confidence >= min_confidence]
    scope_bounds = None
    element_ids: list[str]
    region_items: list[GuiMapRegion]

    if scope_id:
        region = pack.regions.get(scope_id)
        if region is None:
            raise ValueError(f"unknown map scope: {scope_id}")
        scope_bounds = region.scope_bounds
        element_ids = list(region.elements)
        region_items = [region]
        boxes = _boxes_in_scope(boxes, scope_bounds)
    else:
        element_ids = list(pack.elements.keys())
        region_items = list(pack.regions.values())

    matched_box_ids: set[int] = set()
    element_drifts: list[ElementDrift] = []
    counts = {"ok": 0, "fingerprint": 0, "bounds": 0, "missing": 0, "anchor": 0}

    for element_id in element_ids:
        element = pack.elements.get(element_id)
        if element is None:
            continue
        live_box = match_ocr_box_for_element(element, boxes)
        if live_box is None:
            counts["missing"] += 1
            element_drifts.append(
                ElementDrift(
                    element_id=element_id,
                    status="missing",
                    message="OCR anchor not found near stored bounds",
                    stored_bounds=element.raw_bounds.to_dict(),
                    stored_fingerprint=element.tile_fingerprint,
                )
            )
            continue

        matched_box_ids.add(id(live_box))
        live_raw = _box_to_bounds(live_box)
        delta = _distance(element.raw_bounds, live_raw)
        live_fp = tile_fingerprint(png, live_raw)
        stored_fp = element.tile_fingerprint

        if delta > bounds_tolerance_px:
            counts["bounds"] += 1
            element_drifts.append(
                ElementDrift(
                    element_id=element_id,
                    status="bounds",
                    message=f"bounds moved {delta:.1f}px",
                    stored_bounds=element.raw_bounds.to_dict(),
                    live_bounds=live_raw.to_dict(),
                    stored_fingerprint=stored_fp,
                    live_fingerprint=live_fp,
                    delta_px=delta,
                )
            )
            continue

        if stored_fp and live_fp and stored_fp != live_fp:
            counts["fingerprint"] += 1
            element_drifts.append(
                ElementDrift(
                    element_id=element_id,
                    status="fingerprint",
                    message="tile fingerprint changed",
                    stored_bounds=element.raw_bounds.to_dict(),
                    live_bounds=live_raw.to_dict(),
                    stored_fingerprint=stored_fp,
                    live_fingerprint=live_fp,
                    delta_px=delta,
                )
            )
            continue

        counts["ok"] += 1
        element_drifts.append(
            ElementDrift(
                element_id=element_id,
                status="ok",
                message="stable",
                stored_bounds=element.raw_bounds.to_dict(),
                live_bounds=live_raw.to_dict(),
                stored_fingerprint=stored_fp,
                live_fingerprint=live_fp,
                delta_px=delta,
            )
        )

    region_drifts: list[RegionDrift] = []
    for region in region_items:
        live_fp = tile_fingerprint(png, region.scope_bounds)
        if region.fingerprint and live_fp and region.fingerprint != live_fp:
            region_drifts.append(
                RegionDrift(
                    region_id=region.id,
                    status="fingerprint",
                    message="region fingerprint changed",
                    stored_fingerprint=region.fingerprint,
                    live_fingerprint=live_fp,
                )
            )
        else:
            region_drifts.append(
                RegionDrift(
                    region_id=region.id,
                    status="ok",
                    message="stable",
                    stored_fingerprint=region.fingerprint,
                    live_fingerprint=live_fp,
                )
            )

    known_labels = {
        _normalize_label(element.identity.name or "")
        for element in pack.elements.values()
        if element.identity.name
    }
    new_labels = [
        box.text
        for box in boxes
        if id(box) not in matched_box_ids and _normalize_label(box.text) not in known_labels
    ]

    drifted = any(item.status != "ok" for item in element_drifts + region_drifts)
    diff = GuiMapDiff(
        ok=not drifted,
        drifted=drifted,
        elements=element_drifts,
        regions=region_drifts,
        new_ocr_labels=new_labels,
        summary=counts,
    )
    recommendation, actionable, key_targets = assess_map_drift(diff)
    diff.recommendation = recommendation
    diff.actionable = actionable
    diff.key_targets = key_targets
    return diff


def refresh_gui_map(
    pack: GuiMapPack,
    png: bytes,
    capture_meta: dict[str, Any],
    *,
    scope_id: str | None = None,
    min_confidence: float = 0.5,
    add_new: bool = False,
) -> tuple[GuiMapPack, GuiMapDiff]:
    """Update stored bounds/fingerprints from live OCR; optionally append new elements."""
    diff = diff_gui_map(
        pack,
        png,
        capture_meta,
        scope_id=scope_id,
        min_confidence=min_confidence,
    )
    from .vision_ocr import ocr_png

    boxes = [box for box in ocr_png(png) if box.confidence >= min_confidence]
    if scope_id and scope_id in pack.regions:
        boxes = _boxes_in_scope(boxes, pack.regions[scope_id].scope_bounds)

    updated = GuiMapPack.from_dict(pack.to_dict())
    updated.capture_meta = dict(capture_meta)

    for item in diff.elements:
        if item.status == "missing":
            continue
        element = updated.elements.get(item.element_id)
        if element is None:
            continue
        live_box = match_ocr_box_for_element(element, boxes)
        if live_box is None:
            continue
        refreshed = element_from_ocr_box(
            live_box,
            element_id=element.id,
            region_id=element.region_id,
            capture_meta=capture_meta,
            monitor=element.monitor,
            rotation=element.rotation,
            png=png,
        )
        refreshed.notes = element.notes
        refreshed.verify_mode = element.verify_mode
        updated.elements[element.id] = refreshed

    for region in updated.regions.values():
        region.fingerprint = tile_fingerprint(png, region.scope_bounds)

    if add_new and diff.new_ocr_labels:
        from .gui_map import _slug

        used = set(updated.elements.keys())
        region_key = scope_id or (next(iter(updated.regions)) if updated.regions else None)
        region = updated.regions.get(region_key) if region_key else None
        for index, box in enumerate(boxes):
            if _normalize_label(box.text) in {
                _normalize_label(element.identity.name or "")
                for element in updated.elements.values()
                if element.identity.name
            }:
                continue
            base = _slug(box.text or f"new_{index}")
            element_id = base
            suffix = 1
            while element_id in used:
                element_id = f"{base}_{suffix}"
                suffix += 1
            used.add(element_id)
            element = element_from_ocr_box(
                box,
                element_id=element_id,
                region_id=region.id if region else None,
                capture_meta=capture_meta,
                monitor=updated.monitor,
                rotation=updated.rotation,
                png=png,
            )
            element.notes = "added by map refresh"
            updated.elements[element_id] = element
            if region is not None:
                region.elements.append(element_id)

    return updated, diff
