"""Vision backend selection — local OpenCV/Tesseract vs IMGL scene OCR."""

from __future__ import annotations

from typing import Any

from ..application.env_defaults import vision_backend_name


def vision_backend() -> str:
    return vision_backend_name()


def prefer_imgl_backend() -> bool:
    backend = vision_backend()
    if backend in {"imgl"}:
        return True
    if backend in {"local", "tesseract", "opencv"}:
        return False
    try:
        from .imgl_bridge import imgl_available

        return imgl_available()
    except ImportError:
        return False


def prefer_imgl_ocr() -> bool:
    return prefer_imgl_backend()


def ocr_png(png: bytes, *, min_confidence: float = 30.0) -> list[Any]:
    if prefer_imgl_ocr():
        import tempfile
        from pathlib import Path

        from .imgl_bridge import ocr_boxes_from_imgl

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
            handle.write(png)
            temp_path = handle.name
        try:
            boxes = ocr_boxes_from_imgl(temp_path)
            return [box for box in boxes if box.confidence >= min_confidence]
        finally:
            Path(temp_path).unlink(missing_ok=True)

    from ..control.vision_ocr import _ocr_png_local

    return _ocr_png_local(png, min_confidence=min_confidence)


def match_template(
    png: bytes,
    template_png: bytes,
    *,
    threshold: float = 0.85,
    method: str = "ccoeff_normed",
) -> list[Any]:
    if prefer_imgl_backend():
        try:
            from imgl.vision_ops import match_template_png

            from ..control.models import ControlBounds
            from ..control.vision_template import TemplateMatch

            results = match_template_png(
                png,
                template_png,
                threshold=threshold,
                method=method,
            )
            return [
                TemplateMatch(
                    bounds=ControlBounds(x=item.x, y=item.y, width=item.width, height=item.height),
                    confidence=item.confidence,
                    method=item.method,
                )
                for item in results
            ]
        except ImportError:
            if vision_backend() == "imgl":
                raise

    from ..control.vision_template import _match_template_local

    return _match_template_local(
        png,
        template_png,
        threshold=threshold,
        method=method,
    )


def diff_png_bytes(
    before: bytes,
    after: bytes,
    *,
    region: tuple[int, int, int, int] | None = None,
    min_changed_ratio: float = 0.001,
    min_changed_pixels: int = 0,
) -> dict[str, Any]:
    if prefer_imgl_backend():
        try:
            from imgl.vision_ops import diff_png_bytes as imgl_diff

            return imgl_diff(
                before,
                after,
                region=region,
                min_changed_ratio=min_changed_ratio,
                min_changed_pixels=min_changed_pixels,
            )
        except ImportError:
            if vision_backend() == "imgl":
                raise

    from ..control.screenshot_verify import _diff_png_bytes_local

    return _diff_png_bytes_local(
        before,
        after,
        region=region,
        min_changed_ratio=min_changed_ratio,
        min_changed_pixels=min_changed_pixels,
    )


def render_match_overlay(
    png: bytes,
    matches: list[Any],
    *,
    selected_index: int | None = None,
    rejected: list[Any] | None = None,
) -> bytes:
    if prefer_imgl_backend():
        try:
            from imgl.vision_ops import MatchOverlayItem, render_match_overlay_png

            def _to_item(match: Any) -> MatchOverlayItem:
                bounds = match.bounds
                return MatchOverlayItem(
                    index=int(match.index),
                    x=int(bounds.x),
                    y=int(bounds.y),
                    width=int(bounds.width),
                    height=int(bounds.height),
                    label=str(match.label),
                    confidence=float(match.confidence),
                    selected=bool(match.selected),
                    rejected=bool(match.rejected),
                )

            return render_match_overlay_png(
                png,
                [_to_item(item) for item in matches],
                selected_index=selected_index,
                rejected=[_to_item(item) for item in rejected] if rejected else None,
            )
        except ImportError:
            if vision_backend() == "imgl":
                raise

    from ..control.vision_preview import _render_match_overlay_local

    return _render_match_overlay_local(
        png,
        matches,
        selected_index=selected_index,
        rejected=rejected,
    )

