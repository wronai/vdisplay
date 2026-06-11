"""Screenshot template matching for vision provider find/invoke (PR-22)."""

from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import ControlBounds
from .selector import ControlSelector
from .vision_ocr import anchor_spatial_relation


@dataclass(frozen=True)
class TemplateMatch:
    bounds: ControlBounds
    confidence: float
    method: str = "opencv-matchTemplate"

    def to_dict(self) -> dict[str, Any]:
        return {
            "bounds": self.bounds.to_dict(),
            "confidence": self.confidence,
            "method": self.method,
        }


def template_available() -> tuple[bool, str]:
    try:
        import cv2  # noqa: F401
        import numpy  # noqa: F401
    except ImportError:
        return False, "opencv not installed (optional: pip install opencv-python or opencv-python-headless)"
    return True, "opencv template matching available"


def load_template_png(source: str) -> bytes:
    """Load template PNG from a filesystem path or base64 payload."""
    text = (source or "").strip()
    if not text:
        raise ValueError("vision_template is empty")
    path = Path(text).expanduser()
    if path.is_file():
        return path.read_bytes()
    looks_like_path = "/" in text or text.startswith((".", "~"))
    if looks_like_path:
        raise FileNotFoundError(
            f"vision_template file not found: {path} (use an absolute path or crop a PNG snippet first)"
        )
    try:
        return base64.b64decode(text, validate=True)
    except Exception as exc:
        raise ValueError(f"vision_template must be a file path or base64 PNG: {text!r}") from exc


def _png_to_gray_array(png: bytes):
    import numpy as np
    from PIL import Image

    image = Image.open(io.BytesIO(png)).convert("RGB")
    array = np.array(image)
    import cv2

    return cv2.cvtColor(array, cv2.COLOR_RGB2GRAY)


def match_template(
    png: bytes,
    template_png: bytes,
    *,
    threshold: float = 0.85,
    method: str = "ccoeff_normed",
) -> list[TemplateMatch]:
    """Find template occurrences in a screenshot using OpenCV matchTemplate."""
    import os

    from ..application.env_defaults import vision_backend_name

    backend = vision_backend_name()
    if backend != "local":
        try:
            from ..integrations.vision_backend import match_template as delegated

            return delegated(png, template_png, threshold=threshold, method=method)
        except Exception:
            if backend == "imgl":
                raise
    return _match_template_local(png, template_png, threshold=threshold, method=method)


def _match_template_local(
    png: bytes,
    template_png: bytes,
    *,
    threshold: float = 0.85,
    method: str = "ccoeff_normed",
) -> list[TemplateMatch]:
    """Local OpenCV template matching (vdisplay built-in)."""
    ready, reason = template_available()
    if not ready:
        raise RuntimeError(reason)

    import cv2
    import numpy as np

    screen = _png_to_gray_array(png)
    template = _png_to_gray_array(template_png)
    th, tw = template.shape[:2]
    if th <= 0 or tw <= 0:
        raise ValueError("template image has invalid dimensions")
    if screen.shape[0] < th or screen.shape[1] < tw:
        return []

    cv_method = {
        "ccoeff_normed": cv2.TM_CCOEFF_NORMED,
        "sqdiff_normed": cv2.TM_SQDIFF_NORMED,
    }.get(method, cv2.TM_CCOEFF_NORMED)

    result = cv2.matchTemplate(screen, template, cv_method)
    if cv_method == cv2.TM_SQDIFF_NORMED:
        locations = np.where(result <= (1.0 - threshold))
        scores = 1.0 - result[locations]
    else:
        locations = np.where(result >= threshold)
        scores = result[locations]

    matches: list[TemplateMatch] = []
    for y, x, confidence in zip(locations[0], locations[1], scores, strict=False):
        matches.append(
            TemplateMatch(
                bounds=ControlBounds(x=int(x), y=int(y), width=int(tw), height=int(th)),
                confidence=float(confidence),
            )
        )

    if not matches and cv_method != cv2.TM_SQDIFF_NORMED:
        _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(result)
        if float(max_val) >= threshold:
            x, y = max_loc
            matches.append(
                TemplateMatch(
                    bounds=ControlBounds(x=int(x), y=int(y), width=int(tw), height=int(th)),
                    confidence=float(max_val),
                )
            )

    matches.sort(key=lambda item: item.confidence, reverse=True)
    return _dedupe_matches(matches, min_distance=max(tw, th) // 2)[:16]


def _dedupe_matches(matches: list[TemplateMatch], *, min_distance: int) -> list[TemplateMatch]:
    deduped: list[TemplateMatch] = []
    for item in matches:
        cx, cy = item.bounds.center
        if any(
            abs(cx - kept.bounds.center[0]) < min_distance
            and abs(cy - kept.bounds.center[1]) < min_distance
            for kept in deduped
        ):
            continue
        deduped.append(item)
    return deduped


def _search_region_for_relation(
    anchor: ControlBounds,
    rel: str,
    *,
    margin: int = 200,
    pad: int = 8,
    screen_width: int,
    screen_height: int,
) -> ControlBounds:
    rel_norm = (rel or "near").strip().lower()
    if rel_norm == "right_of":
        x = anchor.x + anchor.width + pad
        y = max(0, anchor.y - pad)
        width = margin
        height = anchor.height + (pad * 2)
    elif rel_norm == "below":
        x = max(0, anchor.x - pad)
        y = anchor.y + anchor.height + pad
        width = anchor.width + (pad * 2)
        height = margin
    elif rel_norm == "left_of":
        x = max(0, anchor.x - margin)
        y = max(0, anchor.y - pad)
        width = min(margin, anchor.x - pad) if anchor.x > pad else margin
        height = anchor.height + (pad * 2)
    elif rel_norm == "above":
        x = max(0, anchor.x - pad)
        y = max(0, anchor.y - margin)
        width = anchor.width + (pad * 2)
        height = min(margin, anchor.y - pad) if anchor.y > pad else margin
    else:
        x = max(0, anchor.x - margin)
        y = max(0, anchor.y - margin)
        width = anchor.width + (margin * 2)
        height = anchor.height + (margin * 2)

    width = max(1, min(width, screen_width - x))
    height = max(1, min(height, screen_height - y))
    return ControlBounds(x=x, y=y, width=width, height=height)


def template_find_selector(
    png: bytes,
    selector: ControlSelector,
    *,
    threshold: float | None = None,
) -> list[TemplateMatch]:
    """Find template matches for a selector's ``vision_template`` field."""
    if not selector.vision_template:
        return []
    from .vision_disambiguate import vision_threshold

    effective = threshold if threshold is not None else vision_threshold(selector)
    template_png = load_template_png(selector.vision_template)
    return match_template(png, template_png, threshold=effective)


def match_template_bounds(
    png: bytes,
    template_path: str,
    anchor_box: ControlBounds,
    relation: str,
    *,
    threshold: float = 0.85,
    max_distance: int = 100,
) -> list[TemplateMatch]:
    """Match template on screen and keep hits that satisfy a spatial anchor relation."""
    template_png = load_template_png(template_path)
    matches = match_template(png, template_png, threshold=threshold)
    filtered: list[TemplateMatch] = []
    for item in matches:
        if anchor_spatial_relation(
            item.bounds,
            anchor_box,
            relation,
            near_threshold=max_distance,
        ):
            filtered.append(item)
    return filtered


def template_anchor_find(
    png: bytes,
    *,
    anchor_bounds: ControlBounds,
    rel: str,
    template_png: bytes,
    threshold: float = 0.85,
    margin: int = 200,
) -> list[TemplateMatch]:
    """Match a template inside a spatial region relative to an anchor box."""
    from PIL import Image

    image = Image.open(io.BytesIO(png))
    screen_w, screen_h = image.size
    region = _search_region_for_relation(
        anchor_bounds,
        rel,
        margin=margin,
        screen_width=screen_w,
        screen_height=screen_h,
    )
    cropped = image.crop((region.x, region.y, region.x + region.width, region.y + region.height))
    buf = io.BytesIO()
    cropped.save(buf, format="PNG")
    local_matches = match_template(buf.getvalue(), template_png, threshold=threshold)
    offset: list[TemplateMatch] = []
    for item in local_matches:
        bounds = ControlBounds(
            x=region.x + item.bounds.x,
            y=region.y + item.bounds.y,
            width=item.bounds.width,
            height=item.bounds.height,
        )
        offset.append(TemplateMatch(bounds=bounds, confidence=item.confidence, method=item.method))
    return offset
