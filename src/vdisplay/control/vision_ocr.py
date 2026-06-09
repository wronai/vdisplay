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
