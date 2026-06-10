"""Screenshot OCR helpers for vision provider invoke/find (PR-20)."""

from __future__ import annotations

import io
import re
import shutil
from dataclasses import dataclass
from typing import Any

from .models import ControlBounds
from .selector import ControlSelector


@dataclass(frozen=True)
class OcrTextBox:
    text: str
    bounds: ControlBounds
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "bounds": self.bounds.to_dict(),
            "confidence": self.confidence,
        }


def ocr_available() -> tuple[bool, str]:
    if shutil.which("tesseract") is None:
        return False, "tesseract binary not installed"
    try:
        import pytesseract  # noqa: F401
        from PIL import Image  # noqa: F401
    except ImportError:
        return False, "pytesseract/Pillow not installed (optional: pip install pytesseract Pillow)"
    return True, "tesseract OCR available"


def ocr_png(png: bytes, *, min_confidence: float = 30.0) -> list[OcrTextBox]:
    """Run Tesseract OCR and return text boxes with pixel bounds."""
    ready, reason = ocr_available()
    if not ready:
        raise RuntimeError(reason)

    import pytesseract
    from PIL import Image

    image = Image.open(io.BytesIO(png))
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    boxes: list[OcrTextBox] = []
    count = len(data.get("text", []))
    for index in range(count):
        text = str(data["text"][index] or "").strip()
        if not text:
            continue
        try:
            conf = float(data["conf"][index])
        except (TypeError, ValueError):
            conf = 0.0
        if conf < min_confidence:
            continue
        width = int(data["width"][index])
        height = int(data["height"][index])
        if width <= 0 or height <= 0:
            continue
        boxes.append(
            OcrTextBox(
                text=text,
                bounds=ControlBounds(
                    x=int(data["left"][index]),
                    y=int(data["top"][index]),
                    width=width,
                    height=height,
                ),
                confidence=conf / 100.0,
            )
        )
    return boxes


def _normalize(value: str | None) -> str:
    return (value or "").strip().lower()


def _box_matches(box: OcrTextBox, needle: str, *, exact: bool) -> bool:
    haystack = _normalize(box.text)
    target = _normalize(needle)
    if not target:
        return False
    if exact:
        return haystack == target
    return target in haystack


def match_selector_boxes(
    boxes: list[OcrTextBox],
    selector: ControlSelector,
    *,
    fuzzy: bool = True,
) -> list[OcrTextBox]:
    """Match OCR boxes against vision selector fields.

    Priority: vision_anchor → text (exact) → text_contains → name → name_contains.
    When ``fuzzy`` is True, vision_anchor also matches substring (case-insensitive).
    """
    matches: list[OcrTextBox] = []

    if selector.vision_anchor:
        exact = not fuzzy
        matches = [box for box in boxes if _box_matches(box, selector.vision_anchor, exact=exact)]
        if not matches and fuzzy:
            pattern = re.escape(selector.vision_anchor.strip())
            regex = re.compile(pattern, re.IGNORECASE)
            matches = [box for box in boxes if regex.search(box.text)]
    elif selector.text:
        matches = [box for box in boxes if _box_matches(box, selector.text, exact=True)]
    elif selector.text_contains:
        matches = [box for box in boxes if _box_matches(box, selector.text_contains, exact=False)]
    elif selector.name:
        matches = [box for box in boxes if _box_matches(box, selector.name, exact=True)]
    elif selector.name_contains:
        matches = [box for box in boxes if _box_matches(box, selector.name_contains, exact=False)]

    matches.sort(key=lambda item: item.confidence, reverse=True)
    return matches


def ocr_find_selector(
    png: bytes,
    selector: ControlSelector,
    *,
    min_confidence: float = 30.0,
    fuzzy: bool = True,
) -> tuple[list[OcrTextBox], list[OcrTextBox]]:
    """OCR a screenshot and return (all_boxes, matched_boxes)."""
    boxes = ocr_png(png, min_confidence=min_confidence)
    matched = match_selector_boxes(boxes, selector, fuzzy=fuzzy)
    return boxes, matched


ANCHOR_RELATIONS = frozenset({"right_of", "below", "near", "left_of", "above"})


def _vertical_overlap(a: ControlBounds, b: ControlBounds) -> bool:
    a_top, a_bottom = a.y, a.y + a.height
    b_top, b_bottom = b.y, b.y + b.height
    return a_top < b_bottom and b_top < a_bottom


def _horizontal_overlap(a: ControlBounds, b: ControlBounds) -> bool:
    a_left, a_right = a.x, a.x + a.width
    b_left, b_right = b.x, b.x + b.width
    return a_left < b_right and b_left < a_right


def anchor_spatial_relation(
    candidate: ControlBounds,
    anchor: ControlBounds,
    rel: str,
    *,
    gap: int = 12,
    near_threshold: int = 80,
) -> bool:
    """Return True when ``candidate`` satisfies a spatial relation to ``anchor``."""
    rel_norm = (rel or "near").strip().lower()
    if rel_norm == "right_of":
        return candidate.x >= anchor.x + anchor.width - gap and _vertical_overlap(candidate, anchor)
    if rel_norm == "below":
        return candidate.y >= anchor.y + anchor.height - gap and _horizontal_overlap(candidate, anchor)
    if rel_norm == "left_of":
        return candidate.x + candidate.width <= anchor.x + gap and _vertical_overlap(candidate, anchor)
    if rel_norm == "above":
        return candidate.y + candidate.height <= anchor.y + gap and _horizontal_overlap(candidate, anchor)

    ax, ay = anchor.center
    cx, cy = candidate.center
    distance = ((ax - cx) ** 2 + (ay - cy) ** 2) ** 0.5
    return distance <= near_threshold


def _find_anchor_boxes(
    boxes: list[OcrTextBox],
    anchor_text: str,
    *,
    fuzzy: bool = True,
) -> list[OcrTextBox]:
    selector = ControlSelector(vision_anchor=anchor_text)
    return match_selector_boxes(boxes, selector, fuzzy=fuzzy)


def anchor_spatial_find(
    boxes: list[OcrTextBox],
    *,
    anchor_text: str,
    rel: str,
    target_text: str | None = None,
    fuzzy: bool = True,
) -> tuple[list[OcrTextBox], list[OcrTextBox]]:
    """Find OCR boxes relative to an anchor label using bounds-based geometry."""
    rel_norm = (rel or "near").strip().lower()
    if rel_norm not in ANCHOR_RELATIONS:
        raise ValueError(f"unsupported vision_anchor_rel: {rel!r}")

    anchors = _find_anchor_boxes(boxes, anchor_text, fuzzy=fuzzy)
    if not anchors:
        return anchors, []

    anchor = anchors[0]
    spatial: list[OcrTextBox] = []
    for box in boxes:
        if box is anchor:
            continue
        if not anchor_spatial_relation(box.bounds, anchor.bounds, rel_norm):
            continue
        if target_text and not _box_matches(box, target_text, exact=not fuzzy):
            continue
        spatial.append(box)

    spatial.sort(key=lambda item: item.confidence, reverse=True)
    return anchors, spatial


def anchor_based_find(
    boxes: list[OcrTextBox],
    *,
    anchor_text: str,
    relation: str,
    target_text: str | None = None,
    fuzzy: bool = True,
) -> tuple[list[OcrTextBox], list[OcrTextBox]]:
    """Alias for bounds-based anchor find (PR-22 spec name)."""
    return anchor_spatial_find(
        boxes,
        anchor_text=anchor_text,
        rel=relation,
        target_text=target_text,
        fuzzy=fuzzy,
    )


def ocr_anchor_combined_find(
    png: bytes,
    *,
    template_path: str | None,
    anchor_text: str,
    relation: str,
    target_text: str | None = None,
    template_threshold: float = 0.85,
    min_confidence: float = 30.0,
    fuzzy: bool = True,
) -> list[Any]:
    """Combine OCR anchor resolution with optional template matching near the anchor."""
    from .vision_template import load_template_png, match_template_bounds, template_anchor_find

    all_boxes = ocr_png(png, min_confidence=min_confidence)
    anchors, spatial = anchor_spatial_find(
        all_boxes,
        anchor_text=anchor_text,
        rel=relation,
        target_text=target_text,
        fuzzy=fuzzy,
    )
    if not anchors:
        return []

    if template_path:
        template_matches = template_anchor_find(
            png,
            anchor_bounds=anchors[0].bounds,
            rel=relation,
            template_png=load_template_png(template_path),
            threshold=template_threshold,
        )
        if not template_matches:
            template_matches = match_template_bounds(
                png,
                template_path,
                anchors[0].bounds,
                relation,
                threshold=template_threshold,
            )
        return template_matches

    return spatial
