"""GUI Map Pack — persistent regions/elements with raw vs action bounds (PR-26)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..exceptions import VDisplayError
from .models import ControlBounds


@dataclass(frozen=True)
class GuiMapBounds:
    x: int
    y: int
    width: int
    height: int

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> GuiMapBounds:
        return cls(
            x=int(payload.get("x") or 0),
            y=int(payload.get("y") or 0),
            width=int(payload.get("width") or 0),
            height=int(payload.get("height") or 0),
        )

    def to_dict(self) -> dict[str, int]:
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}

    @classmethod
    def from_control_bounds(cls, bounds: ControlBounds) -> GuiMapBounds:
        return cls(x=bounds.x, y=bounds.y, width=bounds.width, height=bounds.height)

    def to_control_bounds(self) -> ControlBounds:
        return ControlBounds(x=self.x, y=self.y, width=self.width, height=self.height)

    @property
    def center(self) -> tuple[int, int]:
        return self.x + self.width // 2, self.y + self.height // 2


@dataclass(frozen=True)
class GuiMapPoint:
    x: int
    y: int

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> GuiMapPoint:
        return cls(x=int(payload.get("x") or 0), y=int(payload.get("y") or 0))

    def to_dict(self) -> dict[str, int]:
        return {"x": self.x, "y": self.y}


@dataclass(frozen=True)
class GuiMapIdentity:
    role: str | None = None
    name: str | None = None
    name_prefix: str | None = None
    anchor_text: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> GuiMapIdentity:
        payload = payload or {}
        return cls(
            role=payload.get("role"),
            name=payload.get("name"),
            name_prefix=payload.get("name_prefix"),
            anchor_text=payload.get("anchor_text"),
        )

    def to_dict(self) -> dict[str, str | None]:
        return {
            "role": self.role,
            "name": self.name,
            "name_prefix": self.name_prefix,
            "anchor_text": self.anchor_text,
        }


@dataclass
class GuiMapElement:
    id: str
    raw_bounds: GuiMapBounds
    action_bounds: GuiMapBounds
    click_point: GuiMapPoint
    role: str = "unknown"
    identity: GuiMapIdentity = field(default_factory=GuiMapIdentity)
    anchors: list[str] = field(default_factory=list)
    monitor: str | None = None
    rotation: str | None = None
    region_id: str | None = None
    verify_mode: str = "identity+region"
    tile_fingerprint: str | None = None
    capture_meta: dict[str, Any] = field(default_factory=dict)
    notes: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> GuiMapElement:
        return cls(
            id=str(payload["id"]),
            role=str(payload.get("role") or "unknown"),
            raw_bounds=GuiMapBounds.from_dict(payload.get("raw_bounds") or {}),
            action_bounds=GuiMapBounds.from_dict(payload.get("action_bounds") or payload.get("raw_bounds") or {}),
            click_point=GuiMapPoint.from_dict(payload.get("click_point") or {}),
            identity=GuiMapIdentity.from_dict(payload.get("identity")),
            anchors=list(payload.get("anchors") or []),
            monitor=payload.get("monitor"),
            rotation=payload.get("rotation"),
            region_id=payload.get("region_id"),
            verify_mode=str(payload.get("verify_mode") or "identity+region"),
            tile_fingerprint=payload.get("tile_fingerprint"),
            capture_meta=dict(payload.get("capture_meta") or {}),
            notes=payload.get("notes"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "raw_bounds": self.raw_bounds.to_dict(),
            "action_bounds": self.action_bounds.to_dict(),
            "click_point": self.click_point.to_dict(),
            "identity": self.identity.to_dict(),
            "anchors": list(self.anchors),
            "monitor": self.monitor,
            "rotation": self.rotation,
            "region_id": self.region_id,
            "verify_mode": self.verify_mode,
            "tile_fingerprint": self.tile_fingerprint,
            "capture_meta": dict(self.capture_meta),
            "notes": self.notes,
        }


@dataclass
class GuiMapRegion:
    id: str
    label: str
    scope_bounds: GuiMapBounds
    monitor: str | None = None
    rotation: str | None = None
    anchors: list[str] = field(default_factory=list)
    fingerprint: str | None = None
    elements: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> GuiMapRegion:
        return cls(
            id=str(payload["id"]),
            label=str(payload.get("label") or payload["id"]),
            scope_bounds=GuiMapBounds.from_dict(payload.get("scope_bounds") or {}),
            monitor=payload.get("monitor"),
            rotation=payload.get("rotation"),
            anchors=list(payload.get("anchors") or []),
            fingerprint=payload.get("fingerprint"),
            elements=list(payload.get("elements") or []),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "scope_bounds": self.scope_bounds.to_dict(),
            "monitor": self.monitor,
            "rotation": self.rotation,
            "anchors": list(self.anchors),
            "fingerprint": self.fingerprint,
            "elements": list(self.elements),
        }


@dataclass
class GuiMapPack:
    version: int = 1
    monitor: str | None = None
    rotation: str | None = None
    capture_meta: dict[str, Any] = field(default_factory=dict)
    regions: dict[str, GuiMapRegion] = field(default_factory=dict)
    elements: dict[str, GuiMapElement] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> GuiMapPack:
        regions = {
            str(key): GuiMapRegion.from_dict(value)
            for key, value in (payload.get("regions") or {}).items()
        }
        elements = {
            str(key): GuiMapElement.from_dict(value)
            for key, value in (payload.get("elements") or {}).items()
        }
        return cls(
            version=int(payload.get("version") or 1),
            monitor=payload.get("monitor"),
            rotation=payload.get("rotation"),
            capture_meta=dict(payload.get("capture_meta") or {}),
            regions=regions,
            elements=elements,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "monitor": self.monitor,
            "rotation": self.rotation,
            "capture_meta": dict(self.capture_meta),
            "regions": {key: region.to_dict() for key, region in self.regions.items()},
            "elements": {key: element.to_dict() for key, element in self.elements.items()},
        }


def load_gui_map(path: str | Path) -> GuiMapPack:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise VDisplayError(f"invalid GUI map JSON: {path}")
    return GuiMapPack.from_dict(data)


def save_gui_map(path: str | Path, pack: GuiMapPack) -> None:
    Path(path).write_text(json.dumps(pack.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


# Re-exports for backward compatibility
from .gui_map_build import (  # noqa: E402
    _boxes_in_scope_for_build,
    _prepare_ocr_boxes_for_build,
    _slug,
    _translate_ocr_boxes,
    build_gui_map_from_ocr,
    crop_png_bounds,
    element_from_ocr_box,
    parse_crop_bounds,
    tile_fingerprint,
)
from .gui_map_resolve import (  # noqa: E402
    map_element_to_node,
    resolve_map_element,
    resolve_map_region,
    resolve_map_verify_mode,
    scoped_capture_region,
    verify_hints_from_map_element,
)
