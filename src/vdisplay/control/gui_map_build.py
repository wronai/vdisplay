"""GUI Map build functions — OCR → elements, cropping, fingerprinting."""

from __future__ import annotations

import hashlib
import io
import re
from typing import Any

from .action_bounds import action_bounds_for_vision, click_point_for_vision
from .gui_map import (
    GuiMapBounds,
    GuiMapElement,
    GuiMapIdentity,
    GuiMapPack,
    GuiMapPoint,
    GuiMapRegion,
)
from .models import ControlBounds
from .vision_ocr import OcrTextBox


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
        raise ValueError("crop bounds must be x,y,width,height")
    x, y, width, height = (int(part) for part in parts)
    if width <= 0 or height <= 0:
        raise ValueError("crop bounds width and height must be positive")
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
    ocr_png_bytes, offset_x, offset_y = _maybe_crop_png(png, scope, scope_bounds, width, height)

    boxes = _translate_ocr_boxes(ocr_png(ocr_png_bytes), offset_x, offset_y)
    boxes = _filter_ocr_boxes(boxes, min_confidence=min_confidence, min_text_len=min_text_len)
    return _boxes_in_scope_for_build(boxes, scope), scope


def _maybe_crop_png(
    png: bytes,
    scope: GuiMapBounds,
    scope_bounds: GuiMapBounds | None,
    width: int,
    height: int,
) -> tuple[bytes, int, int]:
    if scope_bounds is not None and (
        scope.x > 0 or scope.y > 0 or scope.width < width or scope.height < height
    ):
        return crop_png_bounds(png, scope)
    return png, 0, 0


def _filter_ocr_boxes(
    boxes: list[OcrTextBox],
    *,
    min_confidence: float,
    min_text_len: int,
) -> list[OcrTextBox]:
    return [
        box
        for box in boxes
        if box.confidence >= min_confidence and len((box.text or "").strip()) >= min_text_len
    ]


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
