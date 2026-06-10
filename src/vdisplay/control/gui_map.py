"""GUI Map Pack — persistent regions/elements with raw vs action bounds (PR-26)."""

from __future__ import annotations

import hashlib
import io
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ..exceptions import VDisplayError
from .action_bounds import action_bounds_for_vision, click_point_for_vision
from .models import ControlBounds, ControlNode, ControlRole
from .vision_ocr import OcrTextBox


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


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.strip().lower()).strip("_")
    return slug or "element"


def tile_fingerprint(png: bytes, bounds: GuiMapBounds) -> str | None:
    try:
        from PIL import Image

        image = Image.open(io.BytesIO(png)).convert("L")
        left = max(0, bounds.x)
        top = max(0, bounds.y)
        right = min(image.width, bounds.x + bounds.width)
        bottom = min(image.height, bounds.y + bounds.height)
        if right <= left or bottom <= top:
            return None
        crop = image.crop((left, top, right, bottom)).resize((8, 8))
        digest = hashlib.sha256(bytes(crop.tobytes())).hexdigest()[:16]
        return f"phash:{digest}"
    except Exception:
        return None


def element_from_ocr_box(
    box: OcrTextBox,
    *,
    element_id: str,
    region_id: str | None,
    capture_meta: dict[str, Any],
    monitor: str | None,
    rotation: str | None,
    png: bytes | None = None,
) -> GuiMapElement:
    raw = GuiMapBounds.from_control_bounds(box.bounds)
    action = GuiMapBounds.from_control_bounds(action_bounds_for_vision(box.bounds))
    cx, cy = click_point_for_vision(box.bounds)
    anchors = [box.text] if box.text else []
    return GuiMapElement(
        id=element_id,
        role="textbox" if len(box.text or "") > 12 else "label",
        raw_bounds=raw,
        action_bounds=action,
        click_point=GuiMapPoint(x=cx, y=cy),
        identity=GuiMapIdentity(
            role="textbox" if len(box.text or "") > 12 else "label",
            name=box.text,
            name_prefix=(box.text or "")[:32] or None,
            anchor_text=box.text,
        ),
        anchors=anchors,
        monitor=monitor,
        rotation=rotation,
        region_id=region_id,
        verify_mode="identity+region",
        tile_fingerprint=tile_fingerprint(png, raw) if png else None,
        capture_meta=dict(capture_meta),
        notes="OCR detection; click uses action_bounds",
    )


def crop_png_bounds(
    png: bytes,
    scope: GuiMapBounds,
    *,
    padding: int = 8,
) -> tuple[bytes, int, int]:
    """Crop PNG to scope; return (cropped_png, offset_x, offset_y) in parent coords."""
    from PIL import Image

    image = Image.open(io.BytesIO(png))
    left = max(0, scope.x - padding)
    top = max(0, scope.y - padding)
    right = min(image.width, scope.x + scope.width + padding)
    bottom = min(image.height, scope.y + scope.height + padding)
    if right <= left or bottom <= top:
        return png, 0, 0
    buf = io.BytesIO()
    image.crop((left, top, right, bottom)).save(buf, format="PNG")
    return buf.getvalue(), left, top


def _translate_ocr_boxes(boxes: list[OcrTextBox], offset_x: int, offset_y: int) -> list[OcrTextBox]:
    if offset_x == 0 and offset_y == 0:
        return boxes
    translated: list[OcrTextBox] = []
    for box in boxes:
        bounds = box.bounds
        translated.append(
            OcrTextBox(
                box.text,
                ControlBounds(
                    x=bounds.x + offset_x,
                    y=bounds.y + offset_y,
                    width=bounds.width,
                    height=bounds.height,
                ),
                box.confidence,
            )
        )
    return translated


def parse_crop_bounds(raw: str) -> GuiMapBounds:
    parts = [part.strip() for part in raw.split(",")]
    if len(parts) != 4:
        raise VDisplayError("crop bounds must be x,y,width,height")
    x, y, width, height = (int(part) for part in parts)
    if width <= 0 or height <= 0:
        raise VDisplayError("crop bounds width and height must be positive")
    return GuiMapBounds(x=x, y=y, width=width, height=height)


def _boxes_in_scope_for_build(boxes: list[OcrTextBox], scope: GuiMapBounds) -> list[OcrTextBox]:
    kept: list[OcrTextBox] = []
    for box in boxes:
        bounds = GuiMapBounds.from_control_bounds(box.bounds)
        cx, cy = bounds.center
        if scope.x <= cx <= scope.x + scope.width and scope.y <= cy <= scope.y + scope.height:
            kept.append(box)
    return kept


def _prepare_ocr_boxes_for_build(
    png: bytes,
    capture_meta: dict[str, Any],
    *,
    scope_bounds: GuiMapBounds | None,
    min_confidence: float,
    min_text_len: int,
) -> tuple[list[OcrTextBox], GuiMapBounds]:
    from .vision_ocr import ocr_png

    width = int(capture_meta.get("width") or 0)
    height = int(capture_meta.get("height") or 0)
    full_scope = GuiMapBounds(x=0, y=0, width=width, height=height)
    scope = scope_bounds or full_scope
    ocr_png_bytes = png
    offset_x = 0
    offset_y = 0
    if scope_bounds is not None and (
        scope.x > 0 or scope.y > 0 or scope.width < width or scope.height < height
    ):
        ocr_png_bytes, offset_x, offset_y = crop_png_bounds(png, scope)

    boxes = _translate_ocr_boxes(ocr_png(ocr_png_bytes), offset_x, offset_y)
    boxes = [
        box
        for box in boxes
        if box.confidence >= min_confidence and len((box.text or "").strip()) >= min_text_len
    ]
    return _boxes_in_scope_for_build(boxes, scope), scope


def build_gui_map_from_ocr(
    png: bytes,
    capture_meta: dict[str, Any],
    *,
    monitor: str | None = None,
    rotation: str | None = None,
    region_id: str = "screen",
    region_label: str | None = None,
    min_confidence: float = 0.5,
    scope_bounds: GuiMapBounds | None = None,
    min_text_len: int = 2,
) -> GuiMapPack:
    boxes, scope = _prepare_ocr_boxes_for_build(
        png,
        capture_meta,
        scope_bounds=scope_bounds,
        min_confidence=min_confidence,
        min_text_len=min_text_len,
    )
    pack = GuiMapPack(monitor=monitor, rotation=rotation, capture_meta=dict(capture_meta))
    region = GuiMapRegion(
        id=region_id,
        label=region_label or region_id,
        scope_bounds=scope,
        monitor=monitor,
        rotation=rotation,
        anchors=[box.text for box in boxes[:12] if box.text],
        fingerprint=tile_fingerprint(png, scope),
    )
    used: set[str] = set()
    for index, box in enumerate(boxes):
        base = _slug(box.text or f"box_{index}")
        element_id = base
        suffix = 1
        while element_id in used:
            element_id = f"{base}_{suffix}"
            suffix += 1
        used.add(element_id)
        element = element_from_ocr_box(
            box,
            element_id=element_id,
            region_id=region_id,
            capture_meta=capture_meta,
            monitor=monitor,
            rotation=rotation,
            png=png,
        )
        pack.elements[element_id] = element
        region.elements.append(element_id)
    pack.regions[region_id] = region
    return pack


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
    raw = (element.verify_mode or "identity+region").strip().lower()
    if raw in {"semantic", "structure", "dom", "text", "hybrid"}:
        raw = "identity+region"
    if raw != "identity+region":
        if raw == "ocr":
            return "ocr_contains"
        if raw == "screenshot":
            return "screenshot_diff"
        return raw
    if action == "set_value" and value:
        return "ocr_contains"
    if element.identity.anchor_text:
        return "anchor_visible"
    label = element.identity.name_prefix or element.identity.name
    if label:
        return "ocr_contains"
    return "screenshot_diff"
