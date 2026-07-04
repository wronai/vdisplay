"""Vision LLM: detect IDE chat composer click targets from desktop screenshots.

Used when OCR/VQL layers are empty, polluted, or disagree with the expected IDE window.
Coordinates are PNG-local (top-left origin), suitable for photo-VQL actuation.
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

from .vision_llm import VisionLlmSettings, query_vision_llm, vision_llm_settings

logger = logging.getLogger(__name__)

_MIN_CONFIDENCE = 0.35

# Minimum vertical position (fraction of image height) a JetBrains chat target
# may sit at. The old 0.55 default assumed a *bottom-docked* AI chat panel and
# rejected right-docked panels (Qoder, AI Assistant docked right) whose input
# sits around the vertical middle. 0.25 still rejects clearly-wrong top targets
# (menu bar, editor tabs) but accepts side panels. Override per-layout with
# VDISPLAY_JB_CHAT_MIN_Y_FRAC.
_JB_CHAT_MIN_Y_FRAC_DEFAULT = 0.25


def _jb_chat_min_y_frac() -> float:
    raw = (os.environ.get("VDISPLAY_JB_CHAT_MIN_Y_FRAC") or "").strip()
    if not raw:
        return _JB_CHAT_MIN_Y_FRAC_DEFAULT
    try:
        value = float(raw)
    except ValueError:
        return _JB_CHAT_MIN_Y_FRAC_DEFAULT
    return min(max(value, 0.0), 1.0)

_REJECT_REASON_MARKERS = (
    "could not find",
    "cannot find",
    "can't find",
    "no valid",
    "not displayed",
    "not visible",
    "wrong window",
    "wrong ide",
    "not jetbrains",
    "not pycharm",
    "rejecting would be more accurate",
    "true target not",
)

# Unambiguous competing-IDE names — matched as whole words in the LLM reason.
_WRONG_IDE_MARKERS_FOR_JETBRAINS = (
    "vscodium",
    "vscode",
    "code editor",
    "codium",
)

# "cursor" is ambiguous: the vision model routinely says "based on the text
# cursor" / "the cursor and placeholder" when describing an input field — that
# does NOT mean the Cursor IDE. Only treat it as the competing IDE when it
# carries an app qualifier. Benign phrases (text/mouse/blinking cursor, cursor
# position/blinking) must never trigger a rejection.
# Reject "cursor" only with an explicit app qualifier — a bare "cursor" in the
# reason is almost always the text/mouse cursor, not the Cursor IDE.
_CURSOR_IDE_RE = re.compile(
    r"\bcursor(?:'s)?\s+(?:ide|editor|window|app|application|chat|composer|sidebar)\b"
    r"|\bin\s+cursor\b"
    r"|\bcursor\s+ide\b",
)


def _reason_names_competing_ide(reason: str, *, canon: str) -> str | None:
    if canon not in {"jetbrains", "pycharm", "idea"}:
        return None
    for marker in _WRONG_IDE_MARKERS_FOR_JETBRAINS:
        if re.search(rf"\b{re.escape(marker)}\b", reason):
            return marker
    if _CURSOR_IDE_RE.search(reason):
        return "cursor"
    return None


def llm_decision_rejects_chat_target(
    decision: dict[str, Any],
    *,
    ide: str,
    img_w: int,
    img_h: int,
) -> str | None:
    """Return a rejection reason when vision LLM coords are untrustworthy."""
    canon = _canonical_ide(ide)
    reason = str(decision.get("reason") or "").lower()
    for marker in _REJECT_REASON_MARKERS:
        if marker in reason:
            return f"LLM reason indicates no trustworthy chat target ({marker})"
    competing = _reason_names_competing_ide(reason, canon=canon)
    if competing:
        return f"LLM target references {competing}, not JetBrains chat"
    cc = decision.get("click_center") or {}
    try:
        x = int(cc.get("x", -1))
        y = int(cc.get("y", -1))
    except (TypeError, ValueError):
        return "LLM click_center missing or invalid"
    if img_w > 0 and img_h > 0:
        if x >= int(img_w * 0.97) and y >= int(img_h * 0.97):
            return "LLM coords are bottom-right corner fallback, not chat composer"
        if canon in {"jetbrains", "pycharm", "idea"}:
            min_y = int(img_h * _jb_chat_min_y_frac())
            if y < min_y:
                return (
                    f"LLM y={y} above the chat input zone "
                    f"(min y={min_y} = {_jb_chat_min_y_frac():.2f}·height); "
                    f"raise VDISPLAY_JB_CHAT_MIN_Y_FRAC only if this is a false accept"
                )
    return None


def _truthy(raw: str | None) -> bool:
    return (raw or "").strip().lower() in {"1", "true", "yes", "on"}


def vision_chat_detect_enabled(*, settings: VisionLlmSettings | None = None) -> bool:
    """Whether screenshot chat-target detection via vision LLM is allowed."""
    if _truthy(os.environ.get("VDISPLAY_VISION_CHAT_DETECT")):
        cfg = settings or vision_llm_settings()
        return bool(cfg.api_key)
    cfg = settings or vision_llm_settings()
    return cfg.enabled and bool(cfg.api_key)


def _parse_vision_json(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("\n", 1)[0] if "\n" in text else text.strip("`")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return data if isinstance(data, dict) else None


def _image_size_png(png: bytes) -> tuple[int, int]:
    try:
        from PIL import Image
        import io

        with Image.open(io.BytesIO(png)) as img:
            return img.size
    except Exception:
        return 2048, 1280


def _read_png(path: str | Path) -> bytes | None:
    try:
        return Path(path).expanduser().read_bytes()
    except OSError:
        return None


def _canonical_ide(ide: str) -> str:
    raw = (ide or "auto").strip().lower()
    aliases = {"pycharm": "jetbrains", "idea": "jetbrains", "intellij": "jetbrains", "jb": "jetbrains"}
    return aliases.get(raw, raw)


def _task_hint(canon: str) -> tuple[str, str]:
    if canon in {"jetbrains", "pycharm", "idea"}:
        return (
            "Find the JetBrains/PyCharm/IntelliJ AI chat composer (bottom-right panel). "
            "Look for placeholder text like 'Ask', an empty message box, or the AI assistant input. "
            "Do NOT click the main code editor, file tabs, project tree, or integrated terminal.",
            "REJECT terminal windows, unrelated editors, file tabs, and main editor center. "
            "Prefer bottom-right chat panel (y typically > 55% of image height).",
        )
    if canon in {"cursor", "windsurf", "vscode", "vscodium", "antigravity"}:
        return (
            f"Find the {canon} IDE chat/composer input (often top panel with 'Ask anything' or similar). "
            "Do NOT click the code editor, terminal, or sidebar file tree.",
            "REJECT terminal and bottom taskbar; prefer top chat/composer bar.",
        )
    return (
        "Find the IDE AI chat or prompt composer input field.",
        "REJECT unrelated windows and terminal shells.",
    )


# Distinctive chat-input placeholder tokens per IDE family. Matched against
# word-level OCR; the placeholder sits INSIDE the input box, so its bbox center
# is a safe deterministic click point (no LLM pixel-precision involved).
_CHAT_PLACEHOLDER_TOKENS: dict[str, tuple[str, ...]] = {
    "jetbrains": ("autonomously", "qoder"),  # Qoder: "Plan and build autonomously"
    "cursor": ("anything",),
    "windsurf": ("anything",),
    "vscode": ("copilot",),
    "auto": ("autonomously",),
}


def ocr_anchor_chat_target(png: bytes, *, ide: str = "auto") -> dict[str, Any] | None:
    """Deterministic chat-input target from the OCR bbox of its placeholder text.

    Vision LLMs describe the input correctly but return imprecise pixel coords
    on dense multi-panel screenshots (measured: ~800px off). Tesseract reports
    the placeholder's exact bbox — clicking its center lands inside the input.
    """
    try:
        from .vision_ocr import ocr_available, ocr_png
    except ImportError:
        return None
    ok, _reason = ocr_available()
    if not ok:
        return None
    canon = _canonical_ide(ide)
    tokens = _CHAT_PLACEHOLDER_TOKENS.get(canon) or _CHAT_PLACEHOLDER_TOKENS["auto"]
    try:
        boxes = ocr_png(png, min_confidence=40.0)
    except Exception:
        return None
    _w, img_h = _image_size_png(png)
    # token priority beats OCR reading order: "autonomously" appears only in
    # the input placeholder, while a brand token ("Qoder") also names the
    # panel title bar at the top — skip brand hits in the top strip.
    for token in tokens:
        for box in boxes:
            text = (box.text or "").strip().lower()
            if not text or token not in text:
                continue
            if token in {"qoder", "copilot"} and box.bounds.y < int(img_h * 0.15):
                continue
            if True:
                bounds = box.bounds
                x = int(bounds.x + bounds.width / 2)
                y = int(bounds.y + bounds.height / 2)
                return {
                    "click_center": {
                        "x": x,
                        "y": y,
                        "note": f"ocr anchor: placeholder {box.text!r}",
                    },
                    "id": "ocr:chat-placeholder",
                    "role": "input",
                    "selection_method": "ocr_anchor_chat_placeholder",
                    "ocr_text": box.text,
                    "llm_used": False,
                    # downstream verification reads llm_decision.confidence;
                    # a literal placeholder-bbox hit is as verified as it gets
                    "llm_decision": {
                        "confidence": 0.95,
                        "reason": f"ocr placeholder anchor {box.text!r}",
                        "source": "ocr_anchor",
                        "click_center": {"x": x, "y": y},
                    },
                }
    return None


# Crop cascade: send SMALL regions to the vision LLM in turns instead of one
# dense full-monitor screenshot. Measured on a 2048px multi-panel capture the
# model described the chat input correctly but missed its pixel position by
# ~800px; on a crop the same model is precise. Order: right half first (chat
# panels dock right), then quadrants clockwise from top-right. Each miss costs
# one LLM call; the first accepted hit wins and the crop offset is added back.
_DEFAULT_CROP_PASSES = "right_half,q_tr,q_br,q_bl,q_tl"


def _crop_pass_names() -> list[str]:
    raw = (os.environ.get("VDISPLAY_VISION_CROP_PASSES") or _DEFAULT_CROP_PASSES).strip()
    if raw.lower() in {"0", "off", "none", "false"}:
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def _crop_region(png: bytes, name: str) -> tuple[bytes, int, int] | None:
    """Crop ``name`` region; return (crop_png, dx, dy) or None when unavailable."""
    try:
        import io

        from PIL import Image
    except ImportError:
        return None
    regions = {
        "right_half": (0.5, 0.0, 1.0, 1.0),
        "q_tr": (0.5, 0.0, 1.0, 0.5),
        "q_br": (0.5, 0.5, 1.0, 1.0),
        "q_bl": (0.0, 0.5, 0.5, 1.0),
        "q_tl": (0.0, 0.0, 0.5, 0.5),
    }
    frac = regions.get(name)
    if frac is None:
        return None
    try:
        with Image.open(io.BytesIO(png)) as img:
            w, h = img.size
            left, top = int(w * frac[0]), int(h * frac[1])
            right, bottom = int(w * frac[2]), int(h * frac[3])
            crop = img.crop((left, top, right, bottom))
            buf = io.BytesIO()
            crop.save(buf, format="PNG")
            return buf.getvalue(), left, top
    except Exception:
        return None


def detect_chat_click_target(
    png: bytes,
    *,
    ide: str = "auto",
    source: str = "DP-1",
    candidates: list[dict[str, Any]] | None = None,
    map_hint: dict[str, Any] | None = None,
    capture_title: str | None = None,
    settings: VisionLlmSettings | None = None,
    _crop_pass: bool = False,
) -> dict[str, Any] | None:
    """Return chat input click_center from a full-monitor PNG via OpenRouter vision."""
    if not vision_chat_detect_enabled(settings=settings):
        return None
    if not png:
        return None

    if not _crop_pass:
        anchored = ocr_anchor_chat_target(png, ide=ide)
        if anchored is not None:
            logger.info(
                "vision_chat_detect ocr_anchor ide=%s source=%s x=%s y=%s text=%r",
                _canonical_ide(ide),
                source,
                anchored["click_center"]["x"],
                anchored["click_center"]["y"],
                anchored.get("ocr_text"),
            )
            return anchored
        # crop cascade in turns (small payloads, better pixel precision);
        # the full-image query below is the last resort only
        for pass_name in _crop_pass_names():
            region = _crop_region(png, pass_name)
            if region is None:
                continue
            crop_png, dx, dy = region
            hit = detect_chat_click_target(
                crop_png,
                ide=ide,
                source=source,
                capture_title=capture_title,
                settings=settings,
                _crop_pass=True,
            )
            if hit is None:
                continue
            cc = dict(hit.get("click_center") or {})
            cc["x"] = int(cc.get("x", 0)) + dx
            cc["y"] = int(cc.get("y", 0)) + dy
            hit["click_center"] = cc
            hit["selection_method"] = f"llm_vision_detect_{pass_name}"
            hit["crop_offset"] = {"dx": dx, "dy": dy, "pass": pass_name}
            decision = hit.get("llm_decision")
            if isinstance(decision, dict) and isinstance(decision.get("click_center"), dict):
                decision["click_center"] = {"x": cc["x"], "y": cc["y"]}
            logger.info(
                "vision_chat_detect crop_hit pass=%s ide=%s x=%s y=%s",
                pass_name,
                _canonical_ide(ide),
                cc["x"],
                cc["y"],
            )
            return hit

    cfg = settings or vision_llm_settings()
    canon = _canonical_ide(ide)
    img_w, img_h = _image_size_png(png)
    task_hint, reject_rules = _task_hint(canon)
    ocr_candidates = candidates or []

    text_prompt = (
        f"You analyze a desktop screenshot to drive IDE automation.\n\n"
        f"Expected IDE: {canon}\n"
        f"Monitor/source label: {source}\n"
        f"Screenshot size: {img_w}x{img_h} pixels (origin top-left).\n"
        f"Window title hint from OCR: {capture_title or 'unknown'}\n\n"
        f"TASK: {task_hint}\n"
        f"RULES: {reject_rules}\n\n"
        f"OCR/VQL input candidates (may be polluted — verify visually): "
        f"{json.dumps(ocr_candidates[:8], default=str)}\n"
        f"Map-calibrated hint (optional): {json.dumps((map_hint or {}).get('click_center'))}\n\n"
        f"Return the SINGLE best click_center {{x, y}} IN PNG PIXEL COORDINATES "
        f"(0..{img_w - 1}, 0..{img_h - 1}) inside the editable chat input.\n"
        f"Return ONLY JSON: "
        f'{{"click_center": {{"x": int, "y": int}}, "strategy": str, "confidence": float, "reason": str}}'
    )

    result = query_vision_llm(png, text_prompt, settings=cfg)
    if not result.get("ok"):
        logger.info(
            "vision_chat_detect skipped ide=%s source=%s error=%s",
            canon,
            source,
            str(result.get("error") or "unknown")[:200],
        )
        return None

    raw_text = str(result.get("text") or "")
    decision = _parse_vision_json(raw_text)
    if not decision or "click_center" not in decision:
        logger.info(
            "vision_chat_detect parse_fail ide=%s source=%s text=%s",
            canon,
            source,
            raw_text[:200],
        )
        return None
    conf = float(decision.get("confidence", 0.0))
    reject = llm_decision_rejects_chat_target(decision, ide=canon, img_w=img_w, img_h=img_h)
    if reject:
        logger.info(
            "vision_chat_detect rejected ide=%s source=%s reason=%s llm_reason=%s",
            canon,
            source,
            reject,
            str(decision.get("reason", ""))[:120],
        )
        return None
    if conf < _MIN_CONFIDENCE:
        return None
    cc = decision.get("click_center")
    if not isinstance(cc, dict) or cc.get("x") is None or cc.get("y") is None:
        return None

    x = max(0, min(int(cc["x"]), img_w - 1))
    y = max(0, min(int(cc["y"]), img_h - 1))
    if canon in {"jetbrains", "pycharm", "idea"} and y < int(img_h * _jb_chat_min_y_frac()):
        fallback = None
        if ocr_candidates:
            fallback = (ocr_candidates[0] or {}).get("click_center")
        if not isinstance(fallback, dict) and map_hint:
            fallback = map_hint.get("click_center")
        if isinstance(fallback, dict) and fallback.get("x") is not None:
            x = int(fallback["x"])
            y = int(fallback["y"])
            decision["llm_coord_adjusted"] = True

    logger.info(
        "vision_chat_detect ok ide=%s source=%s x=%s y=%s confidence=%s",
        canon,
        source,
        x,
        y,
        conf,
    )
    return {
        "click_center": {
            "x": x,
            "y": y,
            "note": f"vision LLM detect: {str(decision.get('reason', ''))[:80]}",
        },
        "id": "llm:chat-input",
        "role": "input",
        "llm_decision": decision,
        "llm_used": True,
        "selection_method": "llm_vision_detect",
        "model": result.get("model"),
    }


def probe_chat_click_target(
    png: bytes,
    *,
    ide: str = "auto",
    source: str = "DP-1",
    candidates: list[dict[str, Any]] | None = None,
    map_hint: dict[str, Any] | None = None,
    capture_title: str | None = None,
    settings: VisionLlmSettings | None = None,
) -> dict[str, Any]:
    """Like detect_chat_click_target but always returns diagnostic fields."""
    cfg = settings or vision_llm_settings()
    out: dict[str, Any] = {
        "vision_chat_detect_enabled": vision_chat_detect_enabled(settings=cfg),
        "openrouter_api_key_set": bool(cfg.api_key),
        "model": cfg.model,
    }
    if not out["vision_chat_detect_enabled"]:
        out["error"] = "vision chat detect disabled or missing OPENROUTER_API_KEY"
        return out
    target = detect_chat_click_target(
        png,
        ide=ide,
        source=source,
        candidates=candidates,
        map_hint=map_hint,
        capture_title=capture_title,
        settings=cfg,
    )
    if target is not None:
        out["ok"] = True
        out["target"] = target
        return out

    canon = _canonical_ide(ide)
    img_w, img_h = _image_size_png(png)
    task_hint, reject_rules = _task_hint(canon)
    text_prompt = (
        f"You analyze a desktop screenshot to drive IDE automation.\n\n"
        f"Expected IDE: {canon}\nMonitor/source: {source}\nScreenshot: {img_w}x{img_h}px\n"
        f"TASK: {task_hint}\nRULES: {reject_rules}\n"
        f'Return ONLY JSON: {{"click_center": {{"x": int, "y": int}}, "confidence": float, "reason": str}}'
    )
    llm = query_vision_llm(png, text_prompt, settings=cfg)
    out["llm_ok"] = bool(llm.get("ok"))
    out["llm_error"] = llm.get("error")
    out["llm_text"] = (str(llm.get("text") or "")[:800] or None)
    parsed = _parse_vision_json(str(llm.get("text") or "")) if llm.get("ok") else None
    out["parsed_json"] = parsed
    if parsed and parsed.get("click_center"):
        conf = float(parsed.get("confidence", 0.0))
        out["confidence"] = conf
        reject = llm_decision_rejects_chat_target(parsed, ide=canon, img_w=img_w, img_h=img_h)
        if reject:
            out["error"] = reject
        elif conf < _MIN_CONFIDENCE:
            out["error"] = f"confidence {conf} below minimum {_MIN_CONFIDENCE}"
        else:
            # Coords cleared the guard and confidence floor — the second-pass
            # query succeeded where the first returned None. Accept them as the
            # target instead of erroring (previous behaviour dropped a valid
            # right-docked chat target).
            cc = parsed["click_center"]
            x = max(0, min(int(cc["x"]), img_w - 1))
            y = max(0, min(int(cc["y"]), img_h - 1))
            out["ok"] = True
            out["target"] = {
                "click_center": {
                    "x": x,
                    "y": y,
                    "note": f"vision LLM detect (2nd pass): {str(parsed.get('reason', ''))[:80]}",
                },
                "id": "llm:chat-input",
                "role": "input",
                "llm_decision": parsed,
                "llm_used": True,
                "selection_method": "llm_vision_detect_2nd_pass",
                "model": cfg.model,
            }
            out.pop("error", None)
    elif llm.get("ok"):
        out["error"] = "LLM response missing click_center JSON"
    else:
        out["error"] = str(llm.get("error") or "vision LLM call failed")
    return out


def detect_chat_click_target_from_path(
    image_path: str | Path,
    *,
    ide: str = "auto",
    source: str = "DP-1",
    candidates: list[dict[str, Any]] | None = None,
    map_hint: dict[str, Any] | None = None,
    capture_title: str | None = None,
) -> dict[str, Any] | None:
    """File-path wrapper for :func:`detect_chat_click_target`."""
    png = _read_png(image_path)
    if png is None:
        return None
    return detect_chat_click_target(
        png,
        ide=ide,
        source=source,
        candidates=candidates,
        map_hint=map_hint,
        capture_title=capture_title,
    )


def refine_chat_click_target(
    png: bytes,
    *,
    prompt: str,
    target: dict[str, Any],
    ide: str = "auto",
    source: str = "DP-1",
    candidates: list[dict[str, Any]] | None = None,
    map_hint: dict[str, Any] | None = None,
    capture_title: str | None = None,
) -> tuple[int, int, dict[str, Any] | None]:
    """Refine an existing VQL/map target using vision LLM (coord override)."""
    if str(target.get("selection_method") or "") == "llm_vision_detect" and target.get("llm_decision"):
        cc = target.get("click_center") or {}
        if cc.get("x") is not None:
            return int(cc["x"]), int(cc["y"]), target.get("llm_decision")

    cc = target.get("click_center") or {}
    x = int(cc.get("x", 1024))
    y = int(cc.get("y", 640))
    if not vision_chat_detect_enabled():
        return x, y, None

    detected = detect_chat_click_target(
        png,
        ide=ide,
        source=source,
        candidates=candidates,
        map_hint=map_hint,
        capture_title=capture_title,
    )
    if not detected:
        return x, y, None
    new_cc = detected.get("click_center") or {}
    if new_cc.get("x") is None:
        return x, y, None
    return int(new_cc["x"]), int(new_cc["y"]), detected.get("llm_decision")


__all__ = [
    "detect_chat_click_target",
    "detect_chat_click_target_from_path",
    "llm_decision_rejects_chat_target",
    "probe_chat_click_target",
    "refine_chat_click_target",
    "vision_chat_detect_enabled",
]
