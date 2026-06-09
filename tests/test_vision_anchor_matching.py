"""PR-22 — vision spatial anchor matching (OCR boxes + geometry)."""

from __future__ import annotations

import pytest

from vdisplay.control.models import ControlBounds
from vdisplay.control.providers.vision import VisionStubProvider
from vdisplay.control.selector import ControlSelector
from vdisplay.control.vision_ocr import OcrTextBox, anchor_spatial_find, anchor_spatial_relation


def _boxes() -> list[OcrTextBox]:
    return [
        OcrTextBox("Email", ControlBounds(x=20, y=30, width=50, height=18), 0.95),
        OcrTextBox("Submit", ControlBounds(x=90, y=28, width=60, height=22), 0.93),
        OcrTextBox("Cancel", ControlBounds(x=20, y=70, width=55, height=20), 0.9),
    ]


def test_anchor_spatial_relation_right_of() -> None:
    anchor = ControlBounds(x=20, y=30, width=50, height=18)
    submit = ControlBounds(x=90, y=28, width=60, height=22)
    cancel = ControlBounds(x=20, y=70, width=55, height=20)
    assert anchor_spatial_relation(submit, anchor, "right_of")
    assert not anchor_spatial_relation(cancel, anchor, "right_of")


def test_anchor_spatial_relation_below() -> None:
    anchor = ControlBounds(x=20, y=30, width=50, height=18)
    submit = ControlBounds(x=90, y=28, width=60, height=22)
    cancel = ControlBounds(x=20, y=70, width=55, height=20)
    assert anchor_spatial_relation(cancel, anchor, "below")
    assert not anchor_spatial_relation(submit, anchor, "below")


def test_anchor_spatial_find_right_of_target() -> None:
    anchors, spatial = anchor_spatial_find(
        _boxes(),
        anchor_text="Email",
        rel="right_of",
        target_text="Submit",
    )
    assert len(anchors) == 1
    assert len(spatial) == 1
    assert spatial[0].text == "Submit"


def test_anchor_spatial_find_below_target() -> None:
    anchors, spatial = anchor_spatial_find(
        _boxes(),
        anchor_text="Email",
        rel="below",
        target_text="Cancel",
    )
    assert len(anchors) == 1
    assert len(spatial) == 1
    assert spatial[0].text == "Cancel"


def test_vision_find_anchor_spatial_integration(monkeypatch: pytest.MonkeyPatch) -> None:
    boxes = _boxes()
    monkeypatch.setattr(
        "vdisplay.control.providers.vision.provider.ocr_find_selector",
        lambda *_a, **_k: (boxes, boxes),
    )
    monkeypatch.setattr(
        "vdisplay.control.providers.vision.provider.ocr_available",
        lambda: (True, "tesseract ok"),
    )
    monkeypatch.setattr(
        VisionStubProvider,
        "_capture_png",
        lambda self, **kwargs: (b"png", {"method": "test"}),
    )

    provider = VisionStubProvider()
    nodes = provider.find(
        ControlSelector(
            vision_anchor="Email",
            vision_anchor_rel="right_of",
            vision_target="Submit",
        )
    )
    assert len(nodes) == 1
    assert nodes[0].name == "Submit"
    assert nodes[0].state.get("anchor_rel") == "right_of"
