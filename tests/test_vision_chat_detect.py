from __future__ import annotations

import io

import pytest

from vdisplay.control import vision_chat_detect


def _png(w: int = 2048, h: int = 1280) -> bytes:
    from PIL import Image

    image = Image.new("RGB", (w, h), (30, 30, 30))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def test_vision_chat_detect_enabled_with_explicit_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VDISPLAY_VISION_LLM_ENABLED", raising=False)
    monkeypatch.setenv("VDISPLAY_VISION_CHAT_DETECT", "1")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    assert vision_chat_detect.vision_chat_detect_enabled() is True


def test_detect_chat_click_target_parses_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_VISION_CHAT_DETECT", "1")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")

    monkeypatch.setattr(
        vision_chat_detect,
        "query_vision_llm",
        lambda png, prompt, region=None, settings=None: {
            "ok": True,
            "text": '{"click_center":{"x":1800,"y":1200},"confidence":0.9,"strategy":"chat","reason":"Ask field"}',
            "model": "google/gemini-flash-1.5",
        },
    )

    out = vision_chat_detect.detect_chat_click_target(_png(), ide="jetbrains", source="DP-1")
    assert out is not None
    assert out["id"] == "llm:chat-input"
    assert out["click_center"]["x"] == 1800
    assert out["click_center"]["y"] == 1200


def test_detect_chat_click_target_rejects_cursor_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_VISION_CHAT_DETECT", "1")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")

    monkeypatch.setattr(
        vision_chat_detect,
        "query_vision_llm",
        lambda png, prompt, region=None, settings=None: {
            "ok": True,
            "text": (
                '{"click_center":{"x":959,"y":956},"confidence":0.8,"strategy":"ocr",'
                '"reason":"Could not find JetBrains chat; Cursor editor code block"}'
            ),
            "model": "google/gemini-3.1-flash-image-preview",
        },
    )

    out = vision_chat_detect.detect_chat_click_target(_png(), ide="jetbrains", source="DP-1")
    assert out is None


def test_llm_decision_rejects_corner_fallback() -> None:
    reason = vision_chat_detect.llm_decision_rejects_chat_target(
        {
            "click_center": {"x": 2047, "y": 1279},
            "confidence": 0.8,
            "reason": "No valid JetBrains AI chat on DP-1",
        },
        ide="jetbrains",
        img_w=2048,
        img_h=1280,
    )
    assert reason is not None
    assert "corner" in reason.lower() or "no valid" in reason.lower()


def test_resolve_chat_target_from_screenshot_on_empty_layers(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from pathlib import Path

    from vdisplay.integrations import chat_target

    png_path = Path(tmp_path) / "capture.png"
    png_path.write_bytes(_png())

    monkeypatch.setenv("VDISPLAY_VISION_CHAT_DETECT", "1")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    monkeypatch.setattr(
        chat_target,
        "detect_chat_click_target_from_path",
        lambda *a, **k: {
            "click_center": {"x": 900, "y": 1100},
            "id": "llm:chat-input",
            "role": "input",
            "llm_used": True,
            "selection_method": "llm_vision_detect",
        },
    )

    out = chat_target.resolve_chat_target_from_screenshot(
        png_path,
        ide="jetbrains",
        source="DP-1",
        layers=[],
        capture_validation={"capture_confirmed": False, "ok_for_drive": False},
    )
    assert out is not None
    assert out["id"] == "llm:chat-input"
