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
    # exercises the full-image parse path; keep crop cascade + OCR anchor away
    monkeypatch.setenv("VDISPLAY_VISION_CROP_PASSES", "off")
    monkeypatch.setattr(vision_chat_detect, "ocr_anchor_chat_target", lambda png, **k: None)

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


def test_right_docked_chat_midscreen_accepted() -> None:
    # Qoder / AI Assistant docked right: input sits ~40% down, must NOT be rejected.
    reason = vision_chat_detect.llm_decision_rejects_chat_target(
        {"click_center": {"x": 1230, "y": 643}, "confidence": 0.7, "reason": "chat input"},
        ide="jetbrains",
        img_w=2560,
        img_h=1600,
    )
    assert reason is None


def test_top_of_screen_target_still_rejected() -> None:
    # A target in the top ~10% (menu bar / tabs) is still untrustworthy.
    reason = vision_chat_detect.llm_decision_rejects_chat_target(
        {"click_center": {"x": 1230, "y": 120}, "confidence": 0.7, "reason": "chat input"},
        ide="jetbrains",
        img_w=2560,
        img_h=1600,
    )
    assert reason is not None
    assert "above the chat input zone" in reason


def test_jb_chat_min_y_frac_env_override(monkeypatch) -> None:
    # Raising the floor to 0.55 rejects the mid-screen right-docked target again.
    monkeypatch.setenv("VDISPLAY_JB_CHAT_MIN_Y_FRAC", "0.55")
    reason = vision_chat_detect.llm_decision_rejects_chat_target(
        {"click_center": {"x": 1230, "y": 643}, "confidence": 0.7, "reason": "chat input"},
        ide="jetbrains",
        img_w=2560,
        img_h=1600,
    )
    assert reason is not None
    assert "above the chat input zone" in reason


def test_non_jetbrains_ide_not_subject_to_y_floor() -> None:
    reason = vision_chat_detect.llm_decision_rejects_chat_target(
        {"click_center": {"x": 100, "y": 50}, "confidence": 0.7, "reason": "chat input"},
        ide="vscode",
        img_w=2560,
        img_h=1600,
    )
    assert reason is None


def test_resolve_second_pass_accepts_guard_passing_coords(monkeypatch) -> None:
    """When detect_chat_click_target returns None but the fallback LLM query
    yields guard-passing, confident coords, resolve must accept them."""
    import vdisplay.control.vision_chat_detect as vcd

    monkeypatch.setattr(vcd, "vision_chat_detect_enabled", lambda **k: True)
    monkeypatch.setattr(vcd, "detect_chat_click_target", lambda *a, **k: None)
    monkeypatch.setattr(vcd, "_image_size_png", lambda png: (2560, 1600))
    monkeypatch.setattr(
        vcd,
        "query_vision_llm",
        lambda *a, **k: {"ok": True, "text": '{"click_center": {"x": 1230, "y": 643}, "confidence": 0.7, "reason": "chat input"}', "model": "m"},
    )

    class _Cfg:
        api_key = "k"
        model = "m"
        enabled = True

    out = vcd.probe_chat_click_target(b"\x89PNG", ide="jetbrains", settings=_Cfg())
    assert out.get("ok") is True
    assert out["target"]["click_center"]["x"] == 1230
    assert out["target"]["click_center"]["y"] == 643
    assert out["target"]["selection_method"] == "llm_vision_detect_2nd_pass"


def test_cursor_word_in_reason_not_treated_as_cursor_ide():
    """A vision reason describing 'the cursor and placeholder' (text cursor) must
    NOT be rejected as the Cursor IDE — that false-positive blocked valid Qoder
    detections in JetBrains."""
    from vdisplay.control.vision_chat_detect import _reason_names_competing_ide

    benign = [
        "identified the input box based on the cursor and placeholder text",
        "the text cursor is blinking in the input field",
        "mouse cursor hovering over the composer",
        "cursor position at the bottom of the chat",
        "Qoder AI chat input in PyCharm",
    ]
    for r in benign:
        assert _reason_names_competing_ide(r.lower(), canon="jetbrains") is None, r


def test_explicit_cursor_ide_still_rejected():
    from vdisplay.control.vision_chat_detect import _reason_names_competing_ide

    for r in ["this is the Cursor IDE chat panel", "input box in Cursor editor", "in Cursor the composer"]:
        assert _reason_names_competing_ide(r.lower(), canon="jetbrains") == "cursor", r


def test_other_competing_ides_whole_word():
    from vdisplay.control.vision_chat_detect import _reason_names_competing_ide

    assert _reason_names_competing_ide("this looks like vscode chat", canon="jetbrains") == "vscode"
    assert _reason_names_competing_ide("the vscodium composer", canon="jetbrains") == "vscodium"
    # substring must not match inside another word
    assert _reason_names_competing_ide("transcoded image", canon="jetbrains") is None


def _mk_png(w=200, h=100):
    import io
    from PIL import Image

    img = Image.new("RGB", (w, h), (20, 20, 20))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_ocr_anchor_hits_placeholder(monkeypatch):
    import vdisplay.control.vision_chat_detect as vcd
    from vdisplay.control.models import ControlBounds
    from vdisplay.control.vision_ocr import OcrTextBox

    monkeypatch.setattr("vdisplay.control.vision_ocr.ocr_available", lambda: (True, "ok"))
    monkeypatch.setattr(
        "vdisplay.control.vision_ocr.ocr_png",
        lambda png, **k: [
            OcrTextBox(text="Plan", bounds=ControlBounds(x=1500, y=540, width=40, height=16), confidence=90.0),
            OcrTextBox(text="autonomously...", bounds=ControlBounds(x=1600, y=540, width=120, height=16), confidence=88.0),
        ],
    )
    t = vcd.ocr_anchor_chat_target(_mk_png(), ide="jetbrains")
    assert t is not None
    assert t["selection_method"] == "ocr_anchor_chat_placeholder"
    assert t["click_center"]["x"] == 1660  # bbox center of the placeholder word
    assert t["llm_decision"]["confidence"] >= 0.9


def test_crop_cascade_order_and_offset(monkeypatch):
    import vdisplay.control.vision_chat_detect as vcd

    monkeypatch.setenv("VDISPLAY_VISION_CHAT_DETECT", "1")
    monkeypatch.setattr(vcd, "vision_chat_detect_enabled", lambda **k: True)
    monkeypatch.setattr(vcd, "ocr_anchor_chat_target", lambda png, **k: None)

    png = _mk_png(400, 200)
    calls = []

    def fake_llm(img, prompt, settings=None):
        calls.append(vcd._image_size_png(img))
        # succeed only on the 2nd crop pass (q_tr: 200x100)
        if len(calls) == 2:
            return {"ok": True, "text": '{"click_center": {"x": 10, "y": 60}, "confidence": 0.9, "reason": "chat input"}', "model": "m"}
        return {"ok": True, "text": '{"click_center": {"x": 1, "y": 1}, "confidence": 0.1, "reason": "unsure"}', "model": "m"}

    monkeypatch.setattr(vcd, "query_vision_llm", fake_llm)
    hit = vcd.detect_chat_click_target(png, ide="jetbrains", source="DP-1")
    assert hit is not None
    # q_tr crop of 400x200 starts at (200, 0) → offset added back
    assert hit["click_center"]["x"] == 210
    assert hit["click_center"]["y"] == 60
    assert hit["selection_method"] == "llm_vision_detect_q_tr"
    assert hit["crop_offset"]["pass"] == "q_tr"
    # early exit: right_half missed (low conf), q_tr hit, no further calls
    assert len(calls) == 2


def test_crop_cascade_disabled_via_env(monkeypatch):
    import vdisplay.control.vision_chat_detect as vcd

    monkeypatch.setenv("VDISPLAY_VISION_CROP_PASSES", "off")
    assert vcd._crop_pass_names() == []


def test_crop_region_offsets():
    import vdisplay.control.vision_chat_detect as vcd

    png = _mk_png(400, 200)
    for name, (dx, dy, w, h) in {
        "right_half": (200, 0, 200, 200),
        "q_tr": (200, 0, 200, 100),
        "q_br": (200, 100, 200, 100),
        "q_bl": (0, 100, 200, 100),
        "q_tl": (0, 0, 200, 100),
    }.items():
        crop_png, gx, gy = vcd._crop_region(png, name)
        assert (gx, gy) == (dx, dy), name
        assert vcd._image_size_png(crop_png) == (w, h), name


def test_ocr_anchor_prefers_placeholder_over_panel_title(monkeypatch):
    """'Qoder' also names the panel title bar (top strip); the distinctive
    placeholder token must win regardless of OCR reading order."""
    import vdisplay.control.vision_chat_detect as vcd
    from vdisplay.control.models import ControlBounds
    from vdisplay.control.vision_ocr import OcrTextBox

    monkeypatch.setattr("vdisplay.control.vision_ocr.ocr_available", lambda: (True, "ok"))
    monkeypatch.setattr(vcd, "_image_size_png", lambda png: (2048, 1280))
    monkeypatch.setattr(
        "vdisplay.control.vision_ocr.ocr_png",
        lambda png, **k: [
            # panel title first in reading order (top strip)
            OcrTextBox(text="Qoder", bounds=ControlBounds(x=1430, y=72, width=60, height=16), confidence=95.0),
            OcrTextBox(text="autonomously...", bounds=ControlBounds(x=1570, y=698, width=120, height=16), confidence=88.0),
        ],
    )
    t = vcd.ocr_anchor_chat_target(b"png", ide="jetbrains")
    assert t is not None
    assert "autonomously" in t["ocr_text"]
    assert t["click_center"]["y"] == 706


def test_ocr_anchor_brand_token_skipped_in_top_strip(monkeypatch):
    import vdisplay.control.vision_chat_detect as vcd
    from vdisplay.control.models import ControlBounds
    from vdisplay.control.vision_ocr import OcrTextBox

    monkeypatch.setattr("vdisplay.control.vision_ocr.ocr_available", lambda: (True, "ok"))
    monkeypatch.setattr(vcd, "_image_size_png", lambda png: (2048, 1280))
    monkeypatch.setattr(
        "vdisplay.control.vision_ocr.ocr_png",
        lambda png, **k: [
            OcrTextBox(text="Qoder", bounds=ControlBounds(x=1430, y=72, width=60, height=16), confidence=95.0),
        ],
    )
    # only a title-bar brand hit → no anchor (better fall through to crops/LLM)
    assert vcd.ocr_anchor_chat_target(b"png", ide="jetbrains") is None
