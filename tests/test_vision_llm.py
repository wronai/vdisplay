from __future__ import annotations

import io

import pytest

from vdisplay.control.contracts import VerifySpec
from vdisplay.control.models import ControlBounds, ControlNode, ControlRole, ControlSnapshot
from vdisplay.control.selector import ControlSelector
from vdisplay.control.verifier import VerifierPipeline, VerifyContext
from vdisplay.control import vision_llm


def _png(color: tuple[int, int, int] = (240, 240, 240)) -> bytes:
    from PIL import Image

    image = Image.new("RGB", (64, 64), color)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def test_vision_llm_fallback_enabled_requires_mode_and_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_VISION_LLM_ENABLED", "1")
    monkeypatch.setenv("VDISPLAY_VISION_LLM_MODE", "fallback")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert vision_llm.vision_llm_fallback_enabled() is False

    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    assert vision_llm.vision_llm_fallback_enabled() is True

    monkeypatch.setenv("VDISPLAY_VISION_LLM_MODE", "off")
    assert vision_llm.vision_llm_fallback_enabled() is False


def test_verify_text_in_region_parses_yes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        vision_llm,
        "query_vision_llm",
        lambda png, prompt, region=None, settings=None: {
            "ok": True,
            "text": "YES — the message field contains the expected text.",
            "model": "google/gemini-3.1-flash-image-preview",
        },
    )
    result = vision_llm.verify_text_in_region(_png(), "test-message-from-vdisplay")
    assert result["verified"] is True
    assert result["method"] == "vision_llm"


def test_verifier_vision_llm_fallback_only_when_ocr_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_VISION_LLM_ENABLED", "1")
    monkeypatch.setenv("VDISPLAY_VISION_LLM_MODE", "fallback")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")

    calls: list[str] = []

    def fake_verify_text_in_region(png, expected_text, *, region=None, anchor_label=None):
        calls.append(expected_text)
        return {
            "verified": True,
            "method": "vision_llm",
            "confidence": 0.82,
            "reason": "YES — text visible",
        }

    monkeypatch.setattr(vision_llm, "verify_text_in_region", fake_verify_text_in_region)

    button = ControlNode(
        id="msg",
        backend="vision",
        role=ControlRole.INPUT,
        name="message",
        bounds=ControlBounds(0, 0, 200, 40),
    )
    snapshot = ControlSnapshot(
        backend="vision",
        window_id="win",
        app_label="demo",
        nodes={"msg": button},
        root_ids=["msg"],
    )

    class FakeProvider:
        name = "vision"

        def snapshot(self, **kwargs):
            return snapshot

    pipeline = VerifierPipeline()
    spec = VerifySpec(mode="ocr_contains", expected_text="test-message-from-vdisplay")
    ctx = VerifyContext(
        action_provider=FakeProvider(),
        before_snapshot=snapshot,
        target=button,
        action="set-value",
        selector=ControlSelector(),
        capture_fn=lambda **kwargs: _png(),
        spec=spec,
        verify_mode="ocr_contains",
        value="test-message-from-vdisplay",
    )

    monkeypatch.setattr(
        pipeline,
        "_run_ocr",
        lambda ctx, spec, visual_payload: {
            "verified": False,
            "method": "ocr",
            "reason": "ocr text missing",
            "confidence": 0.0,
        },
    )

    result = pipeline.verify_after_action(ctx)
    assert result.verified is True
    assert result.vision_llm is not None
    assert result.vision_llm["method"] == "vision_llm"
    assert calls == ["test-message-from-vdisplay"]


def test_verifier_skips_vision_llm_when_ocr_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_VISION_LLM_ENABLED", "1")
    monkeypatch.setenv("VDISPLAY_VISION_LLM_MODE", "fallback")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")

    def fail_fallback(*args, **kwargs):
        raise AssertionError("vision LLM must not run when OCR succeeds")

    monkeypatch.setattr(vision_llm, "verify_text_in_region", fail_fallback)

    button = ControlNode(
        id="msg",
        backend="vision",
        role=ControlRole.INPUT,
        name="message",
        bounds=ControlBounds(0, 0, 200, 40),
    )
    snapshot = ControlSnapshot(
        backend="vision",
        window_id="win",
        app_label="demo",
        nodes={"msg": button},
        root_ids=["msg"],
    )

    class FakeProvider:
        name = "vision"

        def snapshot(self, **kwargs):
            return snapshot

    pipeline = VerifierPipeline()
    spec = VerifySpec(mode="ocr_contains", expected_text="hello")
    ctx = VerifyContext(
        action_provider=FakeProvider(),
        before_snapshot=snapshot,
        target=button,
        action="set-value",
        selector=ControlSelector(),
        capture_fn=lambda **kwargs: _png(),
        spec=spec,
        verify_mode="ocr_contains",
        value="hello",
    )

    monkeypatch.setattr(
        pipeline,
        "_run_ocr",
        lambda ctx, spec, visual_payload: {
            "verified": True,
            "method": "ocr",
            "reason": "ocr text matched",
            "confidence": 0.9,
        },
    )

    result = pipeline.verify_after_action(ctx)
    assert result.verified is True
    assert result.vision_llm is None
