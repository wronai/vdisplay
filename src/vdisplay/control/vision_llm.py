"""Cold-path vision LLM — semantic Q&A on screenshot crops (OpenRouter).

For **chat composer click detection** (full-frame PNG coordinates), see
``vdisplay.control.vision_chat_detect`` and ``vdisplay.integrations.chat_target``.

Invoked for verify fallback when local OCR/anchor fails and
``VDISPLAY_VISION_LLM_ENABLED=1``.
"""

from __future__ import annotations

import base64
import os
import re
from dataclasses import dataclass
from typing import Any

from .gui_map import GuiMapBounds, crop_png_bounds


@dataclass(frozen=True)
class VisionLlmSettings:
    enabled: bool
    mode: str
    model: str
    api_key: str | None
    modalities: tuple[str, ...]
    timeout_s: float


def _truthy(raw: str | None) -> bool:
    return (raw or "").strip().lower() in {"1", "true", "yes", "on"}


def _normalize_model(model: str) -> str:
    slug = model.strip()
    if slug.startswith("openrouter/"):
        return slug[len("openrouter/") :]
    return slug


def vision_llm_settings() -> VisionLlmSettings:
    mode = (os.environ.get("VDISPLAY_VISION_LLM_MODE") or "off").strip().lower()
    modalities_raw = (os.environ.get("VDISPLAY_VISION_LLM_MODALITIES") or "image,text").strip()
    modalities = tuple(part.strip() for part in modalities_raw.split(",") if part.strip())
    model = (
        os.environ.get("VDISPLAY_VISION_LLM")
        or "openrouter/google/gemini-3.1-flash-image-preview"
    ).strip()
    timeout_raw = (os.environ.get("VDISPLAY_VISION_LLM_TIMEOUT_S") or "30").strip()
    try:
        timeout_s = float(timeout_raw)
    except ValueError:
        timeout_s = 30.0
    return VisionLlmSettings(
        enabled=_truthy(os.environ.get("VDISPLAY_VISION_LLM_ENABLED")),
        mode=mode,
        model=_normalize_model(model),
        api_key=(os.environ.get("OPENROUTER_API_KEY") or "").strip() or None,
        modalities=modalities,
        timeout_s=timeout_s,
    )


def vision_llm_available() -> tuple[bool, str]:
    settings = vision_llm_settings()
    if not settings.enabled:
        return False, "VDISPLAY_VISION_LLM_ENABLED is off"
    if settings.mode not in {"fallback", "enrich", "both"}:
        return False, f"VDISPLAY_VISION_LLM_MODE={settings.mode!r} (need fallback|enrich|both)"
    if not settings.api_key:
        return False, "OPENROUTER_API_KEY not set"
    return True, f"vision LLM ready ({settings.model}, mode={settings.mode})"


def vision_llm_fallback_enabled() -> bool:
    settings = vision_llm_settings()
    return settings.enabled and settings.mode in {"fallback", "both"} and bool(settings.api_key)


def vision_llm_enrich_enabled() -> bool:
    settings = vision_llm_settings()
    return settings.enabled and settings.mode in {"enrich", "both"} and bool(settings.api_key)


def _png_to_data_url(png: bytes) -> str:
    encoded = base64.b64encode(png).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _parse_yes_no(text: str) -> bool | None:
    lowered = text.strip().lower()
    if re.search(r"\b(yes|true|present|visible|found|match(ed)?)\b", lowered):
        if re.search(r"\b(no|not|missing|absent|false)\b", lowered):
            # ambiguous — prefer explicit no at start
            if lowered.startswith(("no", "not", "false")):
                return False
            return True
        return True
    if re.search(r"\b(no|not|missing|absent|false|unable)\b", lowered):
        return False
    return None


def _tokenize_expected(text: str) -> list[str]:
    parts = re.split(r"[\s\-_]+", text.strip())
    return [part for part in parts if len(part) >= 3]


def query_vision_llm(
    png: bytes,
    prompt: str,
    *,
    region: tuple[int, int, int, int] | GuiMapBounds | None = None,
    settings: VisionLlmSettings | None = None,
) -> dict[str, Any]:
    """Send cropped PNG + prompt to OpenRouter; return text answer."""
    cfg = settings or vision_llm_settings()
    if not cfg.api_key:
        return {"ok": False, "error": "OPENROUTER_API_KEY not set", "method": "vision_llm"}

    image_png = png
    if region is not None:
        if isinstance(region, GuiMapBounds):
            bounds = region
        else:
            x, y, w, h = region
            bounds = GuiMapBounds(x=x, y=y, width=w, height=h)
        image_png, _, _ = crop_png_bounds(png, bounds)

    body: dict[str, Any] = {
        "model": cfg.model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": _png_to_data_url(image_png)}},
                ],
            }
        ],
    }
    if cfg.modalities:
        body["modalities"] = list(cfg.modalities)

    try:
        import httpx

        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {cfg.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/wronai/vdisplay",
                "X-Title": "vdisplay vision-llm",
            },
            json=body,
            timeout=cfg.timeout_s,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        return {"ok": False, "error": str(exc), "method": "vision_llm", "model": cfg.model}

    text = ""
    try:
        text = str(payload["choices"][0]["message"]["content"] or "").strip()
    except (KeyError, IndexError, TypeError):
        pass
    return {
        "ok": bool(text),
        "text": text,
        "method": "vision_llm",
        "model": cfg.model,
        "raw": payload,
    }


def verify_text_in_region(
    png: bytes,
    expected_text: str,
    *,
    region: tuple[int, int, int, int] | GuiMapBounds | None = None,
    anchor_label: str | None = None,
) -> dict[str, Any]:
    """Ask vision LLM whether expected text or anchor is visible in region."""
    label = expected_text or anchor_label or ""
    tokens = _tokenize_expected(label) if label else []
    token_hint = ", ".join(tokens[:5]) if tokens else label
    if anchor_label and not expected_text:
        prompt = (
            f"Look at this UI screenshot region. Is the label or button text "
            f'"{anchor_label}" clearly visible? Answer only YES or NO, then one short reason.'
        )
    else:
        prompt = (
            f"Look at this UI screenshot region. Does it contain the text or these tokens: "
            f'"{label}" (tokens: {token_hint})? Answer only YES or NO, then one short reason.'
        )

    result = query_vision_llm(png, prompt, region=region)
    if not result.get("ok"):
        return {
            "verified": False,
            "method": "vision_llm",
            "reason": result.get("error") or "vision LLM query failed",
            "model": result.get("model"),
        }

    answer = str(result.get("text") or "")
    parsed = _parse_yes_no(answer)
    verified = parsed is True
    confidence = 0.82 if verified else 0.0 if parsed is False else 0.5
    return {
        "verified": verified,
        "method": "vision_llm",
        "expected_text": label,
        "text": answer,
        "confidence": confidence,
        "model": result.get("model"),
        "reason": answer[:240],
    }


def summarize_region(png: bytes, *, region: GuiMapBounds | None = None, question: str | None = None) -> dict[str, Any]:
    """Diagnostic / enrich helper — short NL summary of a crop."""
    prompt = question or (
        "Describe this UI region in 2-3 short sentences: visible controls, input fields, "
        "and any message text. Be factual; do not invent elements."
    )
    result = query_vision_llm(png, prompt, region=region)
    if not result.get("ok"):
        return {"ok": False, "error": result.get("error"), "method": "vision_llm"}
    return {
        "ok": True,
        "text": result.get("text"),
        "method": "vision_llm",
        "model": result.get("model"),
    }
