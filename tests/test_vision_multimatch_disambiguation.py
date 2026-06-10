"""PR-24 — vision multi-match disambiguation (index + confidence thresholds)."""

from __future__ import annotations

import io

import pytest

from vdisplay.application.services import control as control_svc
from vdisplay.control.models import ControlBounds
from vdisplay.control.providers.vision import VisionStubProvider
from vdisplay.control.selector import ControlSelector
from vdisplay.control.vision_disambiguate import filter_by_confidence, pick_by_index, resolve_vision_matches
from vdisplay.control.vision_ocr import OcrTextBox, anchor_spatial_find
from vdisplay.control.vision_template import TemplateMatch, template_available


def _boxes_duplicate_anchors() -> list[OcrTextBox]:
    return [
        OcrTextBox("Email", ControlBounds(x=20, y=30, width=50, height=18), 0.95),
        OcrTextBox("Email", ControlBounds(x=20, y=130, width=50, height=18), 0.94),
        OcrTextBox("Submit", ControlBounds(x=90, y=28, width=60, height=22), 0.93),
        OcrTextBox("Submit", ControlBounds(x=90, y=128, width=60, height=22), 0.92),
    ]


def test_filter_by_confidence_drops_weak_matches() -> None:
    boxes = [
        OcrTextBox("A", ControlBounds(x=0, y=0, width=10, height=10), 0.95),
        OcrTextBox("B", ControlBounds(x=0, y=0, width=10, height=10), 0.70),
    ]
    filtered = filter_by_confidence(boxes, min_confidence=0.9)
    assert len(filtered) == 1
    assert filtered[0].text == "A"


def test_pick_by_index_selects_nth_match() -> None:
    boxes = [
        OcrTextBox("A", ControlBounds(x=0, y=0, width=10, height=10), 0.95),
        OcrTextBox("B", ControlBounds(x=0, y=0, width=10, height=10), 0.90),
    ]
    assert pick_by_index(boxes, 1).text == "B"
    assert pick_by_index(boxes, 9) is None


def test_resolve_vision_matches_applies_threshold_and_sort() -> None:
    boxes = [
        OcrTextBox("Low", ControlBounds(x=0, y=0, width=10, height=10), 0.55),
        OcrTextBox("High", ControlBounds(x=0, y=0, width=10, height=10), 0.99),
        OcrTextBox("Mid", ControlBounds(x=0, y=0, width=10, height=10), 0.88),
    ]
    selector = ControlSelector(vision_anchor="x", vision_min_confidence=0.85, index=1)
    filtered, picked = resolve_vision_matches(boxes, selector)
    assert [item.text for item in filtered] == ["High", "Mid"]
    assert picked is not None
    assert picked.text == "Mid"


def test_anchor_spatial_find_uses_anchor_index() -> None:
    anchors, spatial = anchor_spatial_find(
        _boxes_duplicate_anchors(),
        anchor_text="Email",
        rel="right_of",
        target_text="Submit",
        anchor_index=1,
    )
    assert len(anchors) == 2
    assert len(spatial) == 1
    assert spatial[0].bounds.y == 128


def test_vision_ocr_index_picks_second_submit(monkeypatch: pytest.MonkeyPatch) -> None:
    boxes = [
        OcrTextBox("Submit", ControlBounds(x=10, y=20, width=60, height=22), 0.95),
        OcrTextBox("Submit", ControlBounds(x=10, y=120, width=60, height=22), 0.93),
    ]

    def _ocr_find(_png: bytes, selector: ControlSelector, **_k: object) -> tuple[list[OcrTextBox], list[OcrTextBox]]:
        return boxes, boxes

    monkeypatch.setattr("vdisplay.control.providers.vision.provider.ocr_find_selector", _ocr_find)
    monkeypatch.setattr("vdisplay.control.providers.vision.provider.ocr_available", lambda: (True, "ok"))
    monkeypatch.setattr(
        VisionStubProvider,
        "_capture_png",
        lambda self, **kwargs: (b"png", {}),
    )

    provider = VisionStubProvider()
    nodes = provider.find(ControlSelector(vision_anchor="Submit", index=1))
    assert len(nodes) == 2
    assert nodes[1].bounds.y == 120


def test_resolve_target_spatial_anchor_index_is_anchor_only(monkeypatch: pytest.MonkeyPatch) -> None:
    boxes = _boxes_duplicate_anchors()

    def _combined(_png: bytes, **kwargs: object) -> list[OcrTextBox]:
        _anchors, spatial = anchor_spatial_find(
            boxes,
            anchor_text=str(kwargs.get("anchor_text") or ""),
            rel=str(kwargs.get("relation") or "near"),
            target_text=kwargs.get("target_text"),  # type: ignore[arg-type]
            anchor_index=int(kwargs.get("anchor_index") or 0),
        )
        return spatial

    monkeypatch.setattr("vdisplay.control.providers.vision.provider.ocr_anchor_combined_find", _combined)
    monkeypatch.setattr("vdisplay.control.providers.vision.provider.ocr_available", lambda: (True, "ok"))
    monkeypatch.setattr(
        VisionStubProvider,
        "_capture_png",
        lambda self, **kwargs: (b"png", {}),
    )

    provider = VisionStubProvider()
    selector = ControlSelector(
        vision_anchor="Email",
        vision_anchor_rel="right_of",
        vision_target="Submit",
        index=1,
        backend="vision",
    )
    snapshot = provider.snapshot()
    target = control_svc._resolve_target(provider, snapshot, selector)
    assert target is not None
    assert target.bounds.y == 128


@pytest.mark.skipif(not template_available()[0], reason="opencv not installed")
def test_vision_template_min_confidence_filters(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    from PIL import Image

    template = Image.new("RGB", (10, 10), color=(200, 50, 50))
    tbuf = io.BytesIO()
    template.save(tbuf, format="PNG")
    template_path = tmp_path / "btn.png"
    template_path.write_bytes(tbuf.getvalue())

    screen = Image.new("RGB", (80, 80), color=(240, 240, 240))
    screen.paste(template, (10, 10))
    screen.paste(Image.new("RGB", (10, 10), color=(200, 50, 50)), (50, 50))
    sbuf = io.BytesIO()
    screen.save(sbuf, format="PNG")

    monkeypatch.setattr(
        VisionStubProvider,
        "_capture_png",
        lambda self, **kwargs: (sbuf.getvalue(), {}),
    )
    provider = VisionStubProvider()
    selector = ControlSelector(
        vision_template=str(template_path),
        vision_min_confidence=0.99,
    )
    nodes = provider.find(selector)
    assert len(nodes) >= 1
    assert all(float(node.state.get("confidence") or 0) >= 0.99 for node in nodes)
