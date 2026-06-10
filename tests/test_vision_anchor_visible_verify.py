"""PR-22 — anchor_visible verify mode (template + OCR anchor)."""

from __future__ import annotations

import io

import pytest

from vdisplay.control.contracts import VerifySpec
from vdisplay.control.models import ControlBounds, ControlNode, ControlRole, ControlSnapshot
from vdisplay.control.providers.vision import VisionStubProvider
from vdisplay.control.selector import ControlSelector
from vdisplay.control.verifier import VerifierPipeline, VerifyContext
from vdisplay.control.vision_ocr import OcrTextBox


def _png() -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (80, 40), color=(255, 255, 255)).save(buf, format="PNG")
    return buf.getvalue()


def _template_png() -> bytes:
    from PIL import Image

    image = Image.new("RGB", (12, 12), color=(200, 50, 50))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def _ctx(*, selector: ControlSelector, spec: VerifySpec) -> VerifyContext:
    target = ControlNode(
        id="vision:test",
        backend="vision",
        role=ControlRole.UNKNOWN,
        name="test",
        bounds=ControlBounds(x=0, y=0, width=12, height=12),
    )
    return VerifyContext(
        action_provider=VisionStubProvider(),
        before_snapshot=ControlSnapshot(
            backend="vision",
            window_id=None,
            app_label="test",
            nodes={},
            root_ids=[],
        ),
        target=target,
        action="click",
        selector=selector,
        spec=spec,
        before_png=_png(),
    )


def test_anchor_visible_ocr_anchor_found(monkeypatch: pytest.MonkeyPatch) -> None:
    boxes = [OcrTextBox("Submit", ControlBounds(x=10, y=5, width=40, height=14), 0.92)]

    monkeypatch.setattr(
        "vdisplay.control.verifier.capture_control_screenshot",
        lambda **kwargs: (_png(), {"method": "test"}),
    )
    monkeypatch.setattr("vdisplay.control.vision_ocr.ocr_available", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.vision_ocr.ocr_png", lambda *_a, **_k: boxes)

    result = VerifierPipeline().verify_after_action(
        _ctx(
            selector=ControlSelector(vision_anchor="Submit", environment="vision"),
            spec=VerifySpec(mode="anchor_visible", expected_text="Submit"),
        )
    )
    assert result.verified is True
    assert result.mode == "anchor_visible"
    assert result.visual is not None
    assert result.visual["method"] == "ocr_anchor"


def test_select_verify_provider_vision_uses_anchor_visible() -> None:
    from vdisplay.control.scoring import ProviderScore, select_verify_provider

    candidates = [
        ProviderScore(provider="vision", score=90, eligible=True),
    ]
    provider, mode = select_verify_provider(
        candidates,
        action_provider="vision",
        verify_semantic=True,
        verify_screenshot=False,
    )
    assert provider == "vision"
    assert mode == "anchor_visible"


@pytest.mark.skipif(
    __import__("vdisplay.control.vision_template", fromlist=["template_available"]).template_available()[0]
    is False,
    reason="opencv not installed",
)
def test_anchor_visible_template_found(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    from PIL import Image

    template_path = tmp_path / "btn.png"
    template_path.write_bytes(_template_png())
    screen = Image.new("RGB", (60, 40), color=(240, 240, 240))
    screen.paste(Image.open(io.BytesIO(_template_png())), (20, 10))
    buf = io.BytesIO()
    screen.save(buf, format="PNG")

    monkeypatch.setattr(
        "vdisplay.control.verifier.capture_control_screenshot",
        lambda **kwargs: (buf.getvalue(), {"method": "test"}),
    )

    result = VerifierPipeline().verify_after_action(
        _ctx(
            selector=ControlSelector(vision_template=str(template_path), environment="vision"),
            spec=VerifySpec(mode="anchor_visible", min_confidence=0.85),
        )
    )
    assert result.verified is True
    assert result.visual is not None
    assert result.visual["method"] == "template"
