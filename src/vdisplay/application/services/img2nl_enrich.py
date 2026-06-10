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


def _image_path(payload: dict[str, Any]) -> str | None:
    for key in ("path", "saved"):
        value = payload.get(key)
        if value:
            return str(value)
    return None


def describe_screenshot_image(
    image_path: str | Path,
    *,
    locale: str | None = None,
) -> dict[str, Any]:
    path = Path(image_path).expanduser()
    if not path.is_file():
        return {"ok": False, "error": f"image not found: {path}"}

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
    }
    if metadata_slice_from_result is not None:
        payload["metadata"] = metadata_slice_from_result(result)
    if content_check_from_result is not None:
        payload["content_check"] = content_check_from_result(result)
    return payload


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

    return enriched
