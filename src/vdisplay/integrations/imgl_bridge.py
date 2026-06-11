"""Delegate pixel analysis to IMGL when installed."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .screen_context import ScreenContext


def imgl_enabled() -> bool:
    flag = os.environ.get("VDISPLAY_IMGL", "1").strip().lower()
    return flag not in {"0", "false", "no", "off"}


def imgl_available() -> bool:
    if not imgl_enabled():
        return False
    try:
        import imgl  # noqa: F401

        return True
    except ImportError:
        return False


def analyze_with_imgl(
    image_path: str | Path,
    *,
    lang: str | None = None,
    use_cache: bool = True,
) -> dict[str, Any]:
    path = Path(image_path).expanduser()
    if not path.is_file():
        return {"ok": False, "error": f"image not found: {path}"}
    if not imgl_available():
        return {"ok": False, "error": "imgl not installed (pip install imgl or imgl install vdisplay)"}

    from imgl import ImglConfig, analyze, scene_to_json

    try:
        config = ImglConfig(
            skip_blank_check=os.environ.get("VDISPLAY_IMGL_SKIP_BLANK", "").strip().lower() in {"1", "true", "yes"},
        )
    except TypeError:
        config = ImglConfig()
    lang_value = lang or os.environ.get("VDISPLAY_IMGL_LANG", "eng+pol")

    try:
        if use_cache:
            from imgl.scene_cache import load_or_analyze

            scene = load_or_analyze(str(path), lang=lang_value, config=config)
        else:
            scene = analyze(str(path), lang=lang_value, config=config)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

    scene_json = scene_to_json(scene)
    return {
        "ok": True,
        "scene": scene_json,
        "element_count": len(scene_json.get("elements", []) or []),
        "window_count": len(scene_json.get("windows", []) or []),
        "ocr_count": len(scene_json.get("ocr_boxes", []) or []),
        "source": "imgl",
    }


def _try_imgl_vdisplay_context(ctx: ScreenContext, lang: str | None) -> bool:
    try:
        from imgl.vdisplay_context import from_vdisplay_context

        merged = from_vdisplay_context(ctx.to_dict(), analyze=True, lang=lang or "eng+pol")
        if merged.get("ok"):
            ctx.imgl = {**ctx.imgl, **merged, "source": "imgl"}
            if merged.get("scene"):
                ctx.imgl["scene"] = merged["scene"]
            return True
    except ImportError:
        pass
    return False


def attach_imgl_to_context(ctx: ScreenContext, *, lang: str | None = None) -> ScreenContext:
    if not ctx.image_path:
        return ctx
    if _try_imgl_vdisplay_context(ctx, lang):
        return ctx
    result = analyze_with_imgl(ctx.image_path, lang=lang)
    ctx.imgl = {**ctx.imgl, **result}
    if result.get("ok") and not ctx.nl:
        scene = result.get("scene") or {}
        windows = scene.get("windows") or []
        if windows:
            titles = [str(w.get("title") or "") for w in windows if w.get("title")]
            if titles:
                ctx.nl = f"Screen with windows: {', '.join(titles[:5])}."
    return ctx


def _imgl_item_to_ocr_box(item: dict[str, Any]) -> "OcrTextBox":
    from ..control.models import ControlBounds
    from ..control.vision_ocr import OcrTextBox

    bbox = item.get("bbox") or {}
    x = int(bbox.get("x") or 0)
    y = int(bbox.get("y") or 0)
    w = int(bbox.get("w") or bbox.get("width") or 0)
    h = int(bbox.get("h") or bbox.get("height") or 0)
    return OcrTextBox(
        text=str(item.get("text") or ""),
        bounds=ControlBounds(x=x, y=y, width=w, height=h),
        confidence=float(item.get("confidence") or 0.0),
    )


def ocr_boxes_from_imgl(image_path: str | Path, *, lang: str | None = None) -> list[Any]:
    """Return vdisplay OcrTextBox list from IMGL scene OCR."""
    result = analyze_with_imgl(image_path, lang=lang, use_cache=True)
    if not result.get("ok"):
        raise RuntimeError(result.get("error") or "imgl analyze failed")
    items = (result.get("scene") or {}).get("ocr_boxes") or []
    return [_imgl_item_to_ocr_box(item) for item in items]
