"""PR-25 — vision match preview overlay."""

from __future__ import annotations

import io

import pytest

from vdisplay.application.services import control as control_svc
from vdisplay.control.models import ControlBounds, ControlNode, ControlRole
from vdisplay.control.providers.vision import VisionStubProvider
from vdisplay.control.selector import ControlSelector
from vdisplay.control.vision_ocr import OcrTextBox
from vdisplay.control.vision_preview import (
    PreviewMatch,
    action_pick_index,
    build_vision_preview,
    preview_available,
    preview_matches_from_nodes,
    render_match_overlay,
    write_preview_png,
)


def _fake_png(width: int = 200, height: int = 120) -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (width, height), color=(240, 240, 240)).save(buf, format="PNG")
    return buf.getvalue()


def _vision_node(*, name: str, x: int, y: int, confidence: float) -> ControlNode:
    return ControlNode(
        id=f"vision:ocr:0:{name}",
        backend="vision",
        role=ControlRole.UNKNOWN,
        name=name,
        bounds=ControlBounds(x=x, y=y, width=60, height=24),
        state={"ocr": True, "confidence": confidence},
    )


@pytest.mark.skipif(not preview_available()[0], reason="Pillow not installed")
def test_render_match_overlay_draws_boxes() -> None:
    png = _fake_png()
    matches = [
        PreviewMatch(0, ControlBounds(x=20, y=30, width=50, height=20), "Submit", 0.93, selected=True),
        PreviewMatch(1, ControlBounds(x=20, y=80, width=50, height=20), "Cancel", 0.71),
    ]
    overlay = render_match_overlay(png, matches, selected_index=0)
    assert overlay[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(overlay) > len(png)


@pytest.mark.skipif(not preview_available()[0], reason="Pillow not installed")
def test_build_vision_preview_json_and_file(tmp_path) -> None:
    png = _fake_png()
    nodes = [
        _vision_node(name="Submit", x=10, y=20, confidence=0.95),
        _vision_node(name="Submit", x=10, y=70, confidence=0.88),
    ]
    selector = ControlSelector(vision_anchor="Submit", index=1)
    payload = build_vision_preview(png, nodes, selector=selector)
    assert payload["preview_available"] is True
    assert payload["selected_index"] == 1
    assert len(payload["matches"]) == 2
    assert payload["matches"][1]["selected"] is True

    out = tmp_path / "preview.png"
    write_preview_png(__import__("base64").b64decode(payload["preview_png_base64"]), out)
    assert out.is_file()


def test_action_pick_index_spatial_anchor_uses_zero_for_highlight() -> None:
    selector = ControlSelector(vision_anchor="Email", vision_anchor_rel="right_of", index=2)
    assert action_pick_index(selector) == 0


def test_controls_find_preview_integration(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    if not preview_available()[0]:
        pytest.skip("Pillow not installed")

    boxes = [
        OcrTextBox("Submit", ControlBounds(x=30, y=40, width=60, height=22), 0.95),
        OcrTextBox("Submit", ControlBounds(x=30, y=90, width=60, height=22), 0.80),
    ]

    def _ocr_find(_png: bytes, selector: ControlSelector, **_k: object) -> tuple[list[OcrTextBox], list[OcrTextBox]]:
        return boxes, boxes

    monkeypatch.setattr("vdisplay.control.providers.vision.provider.ocr_find_selector", _ocr_find)
    monkeypatch.setattr("vdisplay.control.providers.vision.provider.ocr_available", lambda: (True, "ok"))
    def _mock_capture(self, **kwargs: object) -> tuple[bytes, dict[str, str]]:
        payload = (_fake_png(), {"method": "test"})
        self._last_capture = payload
        return payload

    monkeypatch.setattr(VisionStubProvider, "_capture_png", _mock_capture)

    out = tmp_path / "preview.png"
    payload = control_svc.controls_find(
        backend="vision",
        vision_anchor="Submit",
        index=1,
        preview=True,
        preview_output=str(out),
        preview_debug=True,
    )
    assert payload["count"] == 2
    assert payload["preview"]["preview_available"] is True
    assert payload["preview"]["preview_path"] == str(out.resolve())
    assert out.is_file()


def test_preview_matches_from_nodes_skips_empty_bounds() -> None:
    node = ControlNode(
        id="vision:stub",
        backend="vision",
        role=ControlRole.UNKNOWN,
        name="stub",
        bounds=ControlBounds(x=0, y=0, width=0, height=0),
        state={"confidence": 0.5},
    )
    assert preview_matches_from_nodes([node], selected_index=0) == []
