"""Vision match preview overlay — debug PNG with numbered bounding boxes (PR-25)."""

from __future__ import annotations

import base64
import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .models import ControlBounds, ControlNode
from .selector import ControlSelector
from .vision_disambiguate import item_confidence, pick_by_index


@dataclass(frozen=True)
class PreviewMatch:
    index: int
    bounds: ControlBounds
    label: str
    confidence: float
    kind: str = "vision"
    selected: bool = False
    rejected: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "label": self.label,
            "confidence": self.confidence,
            "kind": self.kind,
            "selected": self.selected,
            "rejected": self.rejected,
            "bounds": self.bounds.to_dict(),
        }


@dataclass
class VisionPreviewDebug:
    selector: ControlSelector | None = None
    selected_index: int = 0
    raw_match_count: int = 0
    filtered_match_count: int = 0
    rejected: list[PreviewMatch] = field(default_factory=list)
    capture_meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "selected_index": self.selected_index,
            "raw_match_count": self.raw_match_count,
            "filtered_match_count": self.filtered_match_count,
            "rejected": [item.to_dict() for item in self.rejected[:20]],
        }
        if self.selector is not None:
            payload["selector"] = self.selector.to_dict()
            if self.selector.vision_anchor:
                payload["vision_anchor"] = self.selector.vision_anchor
            if self.selector.vision_anchor_rel:
                payload["vision_anchor_rel"] = self.selector.vision_anchor_rel
            if self.selector.vision_target:
                payload["vision_target"] = self.selector.vision_target
            if self.selector.vision_min_confidence is not None:
                payload["vision_min_confidence"] = self.selector.vision_min_confidence
        if self.capture_meta:
            payload["capture"] = dict(self.capture_meta)
        return payload


def preview_available() -> tuple[bool, str]:
    try:
        from PIL import Image  # noqa: F401
        from PIL import ImageDraw  # noqa: F401
    except ImportError:
        return False, "Pillow not installed (optional: pip install Pillow or vdisplay[vision])"
    return True, "Pillow vision preview available"


def action_pick_index(selector: ControlSelector) -> int:
    """Index used for click/find highlight — anchor rel consumes --index on anchors."""
    if selector.vision_anchor_rel:
        return 0
    return max(0, int(selector.index))


def _match_kind(node: ControlNode) -> str:
    state = node.state or {}
    if state.get("template"):
        return "template"
    if state.get("anchor"):
        return "anchor"
    if state.get("ocr"):
        return "ocr"
    return "vision"


def preview_matches_from_nodes(
    nodes: list[ControlNode],
    *,
    selected_index: int,
) -> list[PreviewMatch]:
    preview: list[PreviewMatch] = []
    for index, node in enumerate(nodes):
        if node.bounds is None or node.bounds.width <= 0 or node.bounds.height <= 0:
            continue
        preview.append(
            PreviewMatch(
                index=index,
                bounds=node.bounds,
                label=(node.name or node.id or f"match-{index}")[:48],
                confidence=item_confidence(node),
                kind=_match_kind(node),
                selected=index == selected_index,
            )
        )
    return preview


def confidence_color(confidence: float, *, selected: bool = False, rejected: bool = False) -> tuple[int, int, int]:
    if rejected:
        return (140, 140, 140)
    if selected:
        return (0, 220, 80)
    if confidence >= 0.9:
        return (0, 180, 255)
    if confidence >= 0.75:
        return (255, 180, 0)
    return (255, 70, 70)


def render_match_overlay(
    png: bytes,
    matches: list[PreviewMatch],
    *,
    selected_index: int | None = None,
    rejected: list[PreviewMatch] | None = None,
) -> bytes:
    """Draw numbered bounding boxes and confidence labels on a screenshot."""
    ready, reason = preview_available()
    if not ready:
        raise RuntimeError(reason)

    from PIL import Image, ImageDraw, ImageFont

    base = Image.open(io.BytesIO(png)).convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    try:
        font = ImageFont.load_default(size=12)
    except TypeError:
        font = ImageFont.load_default()

    all_items = list(matches)
    if rejected:
        all_items.extend(rejected)

    for item in all_items:
        bounds = item.bounds
        x1, y1 = bounds.x, bounds.y
        x2, y2 = bounds.x + bounds.width, bounds.y + bounds.height
        selected = item.selected or (
            selected_index is not None and item.index == selected_index and not item.rejected
        )
        color = confidence_color(item.confidence, selected=selected, rejected=item.rejected)
        width = 4 if selected else 2
        draw.rectangle([x1, y1, x2, y2], outline=(*color, 255), width=width)
        prefix = "R" if item.rejected else str(item.index)
        tag = f"#{prefix} {item.confidence:.2f} {item.label}"[:56]
        text_y = max(0, y1 - 14)
        draw.rectangle([x1, text_y, x1 + min(220, len(tag) * 7 + 8), text_y + 14], fill=(0, 0, 0, 180))
        draw.text((x1 + 2, text_y + 1), tag, fill=(*color, 255), font=font)
        cx, cy = bounds.center
        draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=(*color, 255))

    composed = Image.alpha_composite(base, overlay)
    out = io.BytesIO()
    composed.convert("RGB").save(out, format="PNG")
    return out.getvalue()


def build_vision_preview(
    png: bytes,
    nodes: list[ControlNode],
    *,
    selector: ControlSelector,
    debug: VisionPreviewDebug | None = None,
) -> dict[str, Any]:
    """Render overlay PNG + JSON metadata for vision find/diagnose."""
    selected_index = action_pick_index(selector)
    matches = preview_matches_from_nodes(nodes, selected_index=selected_index)
    if matches and selected_index < len(matches):
        matches = [
            PreviewMatch(
                index=item.index,
                bounds=item.bounds,
                label=item.label,
                confidence=item.confidence,
                kind=item.kind,
                selected=item.index == selected_index,
                rejected=item.rejected,
            )
            for item in matches
        ]

    rejected = list(debug.rejected) if debug else []
    overlay_png = render_match_overlay(
        png,
        matches,
        selected_index=selected_index,
        rejected=rejected if rejected else None,
    )

    payload: dict[str, Any] = {
        "preview_available": True,
        "selected_index": selected_index,
        "matches": [item.to_dict() for item in matches],
        "preview_png_base64": base64.b64encode(overlay_png).decode("ascii"),
        "preview_size_bytes": len(overlay_png),
    }
    if debug is not None:
        payload["debug"] = debug.to_dict()
    picked = pick_by_index(nodes, selected_index)
    if picked is not None:
        payload["selected_bounds"] = picked.bounds.to_dict() if picked.bounds else None
    return payload


def write_preview_png(png: bytes, path: str | Path) -> str:
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(png)
    return str(target.resolve())


def decode_preview_png(payload: dict[str, Any]) -> bytes | None:
    encoded = payload.get("preview_png_base64")
    if not encoded:
        return None
    return base64.b64decode(str(encoded))
