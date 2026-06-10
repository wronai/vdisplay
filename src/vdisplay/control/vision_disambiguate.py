"""Vision multi-match disambiguation — index + confidence thresholds (PR-24)."""

from __future__ import annotations

from typing import Any, Protocol, TypeVar

from .models import ControlNode
from .selector import ControlSelector
from .vision_ocr import OcrTextBox
from .vision_template import TemplateMatch

T = TypeVar("T")


class _HasConfidence(Protocol):
    confidence: float


def item_confidence(item: OcrTextBox | TemplateMatch | ControlNode) -> float:
    if isinstance(item, ControlNode):
        raw = item.state.get("confidence")
        if raw is not None:
            return float(raw)
        return 0.0
    return float(item.confidence)


def filter_by_confidence(
    matches: list[T],
    *,
    min_confidence: float | None,
) -> list[T]:
    """Drop matches below ``min_confidence`` (0.0–1.0 unified scale)."""
    if min_confidence is None:
        return list(matches)
    threshold = max(0.0, min(1.0, float(min_confidence)))
    return [item for item in matches if item_confidence(item) >= threshold]  # type: ignore[arg-type]


def pick_by_index(matches: list[T], index: int) -> T | None:
    if not matches:
        return None
    idx = max(0, int(index))
    if idx >= len(matches):
        return None
    return matches[idx]


def resolve_vision_matches(
    matches: list[T],
    selector: ControlSelector,
) -> tuple[list[T], T | None]:
    """Filter by ``vision_min_confidence``, then pick ``selector.index``."""
    filtered = filter_by_confidence(matches, min_confidence=selector.vision_min_confidence)
    filtered.sort(key=lambda item: item_confidence(item), reverse=True)  # type: ignore[arg-type]
    picked = pick_by_index(filtered, selector.index)
    return filtered, picked


def vision_threshold(selector: ControlSelector, *, default: float = 0.85) -> float:
    """Template/OCR unified threshold — explicit selector wins, else default."""
    if selector.vision_min_confidence is not None:
        return max(0.0, min(1.0, float(selector.vision_min_confidence)))
    return default


def disambiguation_meta(
    *,
    match_count: int,
    selected_index: int | None,
    min_confidence: float | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"match_count": match_count}
    if selected_index is not None:
        payload["selected_index"] = selected_index
    if min_confidence is not None:
        payload["min_confidence"] = min_confidence
    return payload
