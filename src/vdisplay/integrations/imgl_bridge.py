"""Delegate pixel analysis to IMGL when installed."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable

from .screen_context import ScreenContext
from ..application.env_defaults import env_flag, env_value


def imgl_enabled() -> bool:
    return env_flag("VDISPLAY_IMGL", default=True)


def _import_imgl_api() -> tuple[Any, Callable[..., Any], Callable[..., Any]] | None:
    """Return (ImglConfig, analyze, scene_to_json) when IMGL is usable."""
    try:
        from imgl import ImglConfig, analyze, scene_to_json
    except ImportError:
        try:
            from imgl.config import ImglConfig
            from imgl.export import scene_to_json
            from imgl.pipeline import analyze
        except ImportError:
            return None
    return ImglConfig, analyze, scene_to_json


def imgl_available() -> bool:
    if not imgl_enabled():
        return False
    return _import_imgl_api() is not None


def _vql_sidecar_path(image_path: Path) -> Path:
    return image_path.with_suffix(image_path.suffix + ".vql.json")


def _build_imgl_config(ImglConfig: Any) -> Any:
    skip_blank = env_flag("VDISPLAY_IMGL_SKIP_BLANK", default=False)
    try:
        return ImglConfig(skip_blank=skip_blank)
    except TypeError:
        return ImglConfig()


def _scene_to_dict(scene: Any, scene_to_json: Callable[..., Any]) -> dict[str, Any]:
    """Convert imgl Scene object to dict. scene_to_json may return str or dict."""
    if hasattr(scene, "to_dict"):
        payload = scene.to_dict()
        return payload if isinstance(payload, dict) else {}
    payload = scene_to_json(scene)
    if isinstance(payload, str):
        loaded = json.loads(payload)
        return loaded if isinstance(loaded, dict) else {}
    return payload if isinstance(payload, dict) else {}


def analyze_with_imgl(
    image_path: str | Path,
    *,
    lang: str | None = None,
    use_cache: bool = True,
    vql_file: str | Path | None = None,
) -> dict[str, Any]:
    path = Path(image_path).expanduser()
    if not path.is_file():
        return {"ok": False, "error": f"image not found: {path}"}
    api = _import_imgl_api()
    if api is None:
        return {"ok": False, "error": "imgl not installed (pip install imgl or imgl install vdisplay)"}

    ImglConfig, analyze, scene_to_json = api
    config = _build_imgl_config(ImglConfig)
    lang_value = lang or env_value("VDISPLAY_IMGL_LANG")
    vql_path = Path(vql_file) if vql_file else _vql_sidecar_path(path)

    try:
        if use_cache:
            from imgl.scene_cache import load_or_analyze

            scene = load_or_analyze(
                str(path),
                vql_file=str(vql_path),
                lang=lang_value,
                config=config,
            )
        else:
            scene = analyze(str(path), lang=lang_value, config=config)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

    scene_json = _scene_to_dict(scene, scene_to_json)
    # Count all elements: inside windows + top-level + orphan
    windows = scene_json.get("windows", [])
    elements_in_windows = sum(len(w.get("elements", [])) for w in windows)
    top_elements = len(scene_json.get("elements", []) or [])
    orphan_elements = len(scene_json.get("orphan_elements", []) or [])
    total_elements = elements_in_windows + top_elements + orphan_elements
    return {
        "ok": True,
        "scene": scene_json,
        "element_count": total_elements,
        "window_count": len(windows),
        "ocr_count": len(scene_json.get("ocr_boxes", []) or []),
        "source": "imgl",
        "vql_file": str(vql_path),
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
