"""Optional img2nl enrichment for screenshot command results."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def img2nl_enabled() -> bool:
    flag = os.environ.get("VDISPLAY_IMG2NL", "1").strip().lower()
    return flag not in {"0", "false", "no", "off"}


def img2nl_locale() -> str:
    return os.environ.get("VDISPLAY_IMG2NL_LOCALE", "pl").strip() or "pl"


def describe_backend() -> str:
    return os.environ.get("VDISPLAY_DESCRIBE_BACKEND", "auto").strip().lower() or "auto"


def _extract_window_titles(scene: dict[str, Any]) -> list[str]:
    windows = scene.get("windows") or []
    titles = [str(item.get("title") or "").strip() for item in windows if isinstance(item, dict)]
    return [title for title in titles if title]


def _extract_element_labels(scene: dict[str, Any]) -> list[str]:
    elements = scene.get("elements") or []
    labels = [
        str(item.get("text") or item.get("label") or "").strip()
        for item in elements
        if isinstance(item, dict)
    ]
    return [label for label in labels if label]


def _nl_from_imgl_scene(scene: dict[str, Any] | None) -> str:
    if not isinstance(scene, dict):
        return ""
    titles = _extract_window_titles(scene)
    if titles:
        return f"Screen with windows: {', '.join(titles[:5])}."
    labels = _extract_element_labels(scene)
    if labels:
        return f"UI elements: {', '.join(labels[:8])}."
    return ""


def _describe_via_imgl(image_path: str | Path, *, locale: str | None = None) -> dict[str, Any] | None:
    try:
        from ...integrations.imgl_bridge import analyze_with_imgl, imgl_available
    except ImportError:
        return None
    if not imgl_available():
        return None
    result = analyze_with_imgl(image_path, lang=locale or img2nl_locale(), use_cache=True)
    if not result.get("ok"):
        return None
    scene = result.get("scene") or {}
    text = _nl_from_imgl_scene(scene)
    if not text:
        return None
    return {
        "ok": True,
        "text": text,
        "locale": locale or img2nl_locale(),
        "scene_class": (result.get("img2nl") or {}).get("scene_class", "") or "imgl_scene",
        "source": "imgl",
        "metadata": {"scene": scene, "element_count": result.get("element_count")},
    }


def _describe_via_vql(image_path: str | Path, *, locale: str | None = None) -> dict[str, Any] | None:
    try:
        from img2vql import describe_ui_layout, detect_ui_elements
    except ImportError:
        return None
    path = Path(image_path).expanduser()
    if not path.is_file():
        return None
    detection = detect_ui_elements(str(path))
    if not detection.get("ok"):
        return None
    text = describe_ui_layout(detection, locale=locale or img2nl_locale())
    if not text:
        return None
    return {
        "ok": True,
        "text": text,
        "locale": locale or img2nl_locale(),
        "scene_class": "vql_detection",
        "source": "img2vql",
        "metadata": {"detection": detection},
    }


def describe_screenshot_image(
    image_path: str | Path,
    *,
    locale: str | None = None,
) -> dict[str, Any]:
    path = Path(image_path).expanduser()
    if not path.is_file():
        return {"ok": False, "error": f"image not found: {path}"}

    backend = describe_backend()
    if backend in {"auto", "imgl"}:
        imgl_result = _describe_via_imgl(path, locale=locale)
        if imgl_result is not None:
            return imgl_result
        if backend == "imgl":
            return {"ok": False, "error": "imgl describe failed or unavailable"}

    if backend in {"auto", "vql", "img2vql"}:
        vql_result = _describe_via_vql(path, locale=locale)
        if vql_result is not None:
            return vql_result
        if backend in {"vql", "img2vql"}:
            return {"ok": False, "error": "img2vql describe failed or unavailable"}

    if backend == "img2nl":
        return _describe_via_img2nl(path, locale=locale)

    imgl_result = _describe_via_imgl(path, locale=locale)
    if imgl_result is not None:
        return imgl_result
    vql_result = _describe_via_vql(path, locale=locale)
    if vql_result is not None:
        return vql_result
    return _describe_via_img2nl(path, locale=locale)


def _describe_via_img2nl(
    path: Path,
    *,
    locale: str | None = None,
) -> dict[str, Any]:
    try:
        from img2nl.analyze import analyze_image
    except ImportError:
        from ...utils import auto_install_package
        try:
            auto_install_package("img2nl[analyze]")
            from img2nl.analyze import analyze_image
        except Exception as exc:
            return {
                "ok": False,
                "error": f"img2nl auto-install failed: {exc}",
            }

    try:
        from img2nl.vql_bridge import content_check_from_result, metadata_slice_from_result
    except ImportError:
        content_check_from_result = None
        metadata_slice_from_result = None

    result = analyze_image(
        path,
        locale=locale or img2nl_locale(),
        skip_thumbnail=True,
        goal="describe",
    )
    if not result.ok:
        return {"ok": False, "error": result.error or "img2nl analyze failed"}

    payload: dict[str, Any] = {
        "ok": True,
        "text": result.text,
        "locale": result.locale,
        "scene_class": result.features.get("scene", {}).get("scene_class", ""),
        "llm_hint": result.llm_hint,
        "source": "img2nl",
    }
    if metadata_slice_from_result is not None:
        payload["metadata"] = metadata_slice_from_result(result)
    if content_check_from_result is not None:
        payload["content_check"] = content_check_from_result(result)
    return payload


def _image_path(payload: dict[str, Any]) -> str | None:
    for key in ("path", "saved"):
        value = payload.get(key)
        if value:
            return str(value)
    return None


def _maybe_vision_llm_enrich(image_path: str | Path) -> dict[str, Any] | None:
    from ...control.vision_llm import summarize_region, vision_llm_enrich_enabled

    if not vision_llm_enrich_enabled():
        return None

    path = Path(image_path).expanduser()
    if not path.is_file():
        return None

    try:
        png = path.read_bytes()
    except OSError as exc:
        return {"ok": False, "error": str(exc), "method": "vision_llm"}

    return summarize_region(png)


def enrich_screenshot_payload(payload: dict[str, Any]) -> dict[str, Any]:
    image_path = _image_path(payload)
    if image_path is None and isinstance(payload.get("captures"), list):
        enriched = dict(payload)
        enriched["captures"] = [
            enrich_screenshot_payload(item) if isinstance(item, dict) else item
            for item in payload["captures"]
        ]
        return enriched

    if image_path is None:
        return payload

    enriched = dict(payload)

    if img2nl_enabled():
        analysis = describe_screenshot_image(image_path)
        if analysis:
            enriched["img2nl"] = analysis
            if analysis.get("ok"):
                enriched["nl"] = analysis.get("text", "")

    vision_llm = _maybe_vision_llm_enrich(image_path)
    if vision_llm:
        enriched["vision_llm"] = vision_llm
        if vision_llm.get("ok") and not enriched.get("nl"):
            enriched["nl"] = vision_llm.get("text", "")

    try:
        from ...integrations.pipeline import enrich_capture_payload, observe_enabled

        if observe_enabled():
            enriched = enrich_capture_payload(enriched)
    except ImportError:
        pass

    return enriched
