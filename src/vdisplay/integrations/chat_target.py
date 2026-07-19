"""Resolve IDE chat input targets from screenshot + VQL layers (vision LLM + validation)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..control.vision_chat_detect import (
    detect_chat_click_target_from_path,
    vision_chat_detect_enabled,
)
from ..control.vision_llm import vision_llm_settings
from .vql_capture_validation import (
    ide_window_warning,
    validate_vql_capture,
    window_titles_from_layers,
)


def _chat_input_candidates(layers: list[dict[str, Any]], *, limit: int = 8) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        role = str(layer.get("role") or layer.get("kind") or "").lower()
        if role not in {"input", "textfield", "textarea", "combobox"}:
            continue
        cc = layer.get("click_center") or layer.get("center")
        if not isinstance(cc, dict):
            continue
        candidates.append(
            {
                "id": layer.get("id"),
                "role": role,
                "label": layer.get("label") or layer.get("text"),
                "click_center": cc,
            }
        )
        if len(candidates) >= limit:
            break
    return candidates


def _capture_title_from_layers(layers: list[dict[str, Any]]) -> str | None:
    titles = window_titles_from_layers(layers)
    return titles[0] if titles else None


def should_use_llm_chat_detect(
    *,
    ide: str,
    layers: list[dict[str, Any]],
    capture_validation: dict[str, Any] | None = None,
    polluted: bool = False,
) -> bool:
    """True when VQL/OCR is untrustworthy and vision LLM should locate chat."""
    if not vision_chat_detect_enabled():
        return False
    empty = len(layers) == 0
    if empty or polluted:
        return True
    validation = capture_validation or {}
    if validation.get("capture_confirmed") is False:
        return True
    if validation.get("ok_for_drive") is False:
        return True
    mismatch = ide_window_warning(ide=ide, layers=layers)
    return mismatch is not None


def diagnose_chat_target_resolution(
    image_path: str | Path,
    *,
    ide: str = "auto",
    source: str = "DP-1",
    layers: list[dict[str, Any]] | None = None,
    capture_validation: dict[str, Any] | None = None,
    polluted: bool = False,
) -> dict[str, Any]:
    """Explain why chat-target LLM detection would run or return None."""
    path = Path(image_path).expanduser()
    layers = list(layers or [])
    cfg = vision_llm_settings()
    out: dict[str, Any] = {
        "image_path": str(path),
        "image_exists": path.is_file(),
        "vision_chat_detect_enabled": vision_chat_detect_enabled(),
        "openrouter_api_key_set": bool(cfg.api_key),
        "vision_llm_model": cfg.model,
        "should_use_llm": should_use_llm_chat_detect(
            ide=ide,
            layers=layers,
            capture_validation=capture_validation,
            polluted=polluted,
        ),
        "layers_count": len(layers),
    }
    if not path.is_file():
        out["error"] = "capture PNG not found — run: koru autopilot prepare-vdisplay --ide jetbrains"
        return out
    if not out["vision_chat_detect_enabled"]:
        out["error"] = (
            "vision chat detect disabled — export VDISPLAY_VISION_CHAT_DETECT=1 "
            "(or VDISPLAY_VISION_LLM_ENABLED=1) and OPENROUTER_API_KEY in this shell"
        )
        return out
    if not out["should_use_llm"]:
        out["error"] = "LLM detect not needed (layers trusted and capture confirmed)"
        return out
    png = path.read_bytes()
    from ..control.vision_chat_detect import probe_chat_click_target

    candidates = _chat_input_candidates(layers)
    capture_title = None
    if capture_validation:
        titles = capture_validation.get("window_titles") or []
        capture_title = titles[0] if titles else None
    if not capture_title:
        capture_title = _capture_title_from_layers(layers)

    probe = probe_chat_click_target(
        png,
        ide=ide,
        source=source,
        candidates=candidates,
        map_hint=None,
        capture_title=capture_title,
    )
    if probe.get("ok"):
        target = probe.get("target") or {}
        decision = target.get("llm_decision") if isinstance(target.get("llm_decision"), dict) else {}
        try:
            from ..control.vision_chat_detect import llm_decision_rejects_chat_target
            from PIL import Image
            import io

            with Image.open(io.BytesIO(png)) as img:
                img_w, img_h = img.size
        except Exception:
            img_w, img_h = 2048, 1280
        reject = llm_decision_rejects_chat_target(decision, ide=ide, img_w=img_w, img_h=img_h)
        if reject:
            out["ok"] = False
            out["error"] = reject
            out["target"] = target
            out["llm_decision"] = decision
            return out
        out["ok"] = True
        out["target"] = target
        return out
    out["llm_ok"] = probe.get("llm_ok")
    out["llm_error"] = probe.get("llm_error")
    out["llm_text"] = probe.get("llm_text")
    out["parsed_json"] = probe.get("parsed_json")
    out["confidence"] = probe.get("confidence")
    out["error"] = probe.get("error") or "LLM detect failed"
    return out


def resolve_chat_target_from_screenshot(
    image_path: str | Path,
    *,
    ide: str = "auto",
    source: str = "DP-1",
    layers: list[dict[str, Any]] | None = None,
    capture_validation: dict[str, Any] | None = None,
    map_hint: dict[str, Any] | None = None,
    polluted: bool = False,
) -> dict[str, Any] | None:
    """Detect chat composer via vision LLM when layers/validation are unreliable."""
    layers = list(layers or [])
    if not should_use_llm_chat_detect(
        ide=ide,
        layers=layers,
        capture_validation=capture_validation,
        polluted=polluted,
    ):
        return None

    candidates = _chat_input_candidates(layers)
    capture_title = None
    if capture_validation:
        titles = capture_validation.get("window_titles") or []
        capture_title = titles[0] if titles else None
    if not capture_title:
        capture_title = _capture_title_from_layers(layers)

    return detect_chat_click_target_from_path(
        image_path,
        ide=ide,
        source=source,
        candidates=candidates,
        map_hint=map_hint,
        capture_title=capture_title,
    )


def analyze_capture_for_chat(
    *,
    ide: str,
    layers: list[dict[str, Any]] | None = None,
    nl: str | None = None,
) -> dict[str, Any]:
    """Run vdisplay capture validation (window title, structure, chat hints)."""
    layers = list(layers or [])
    return validate_vql_capture(layers=layers, ide=ide, nl=nl)


__all__ = [
    "analyze_capture_for_chat",
    "diagnose_chat_target_resolution",
    "resolve_chat_target_from_screenshot",
    "should_use_llm_chat_detect",
]
