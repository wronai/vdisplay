"""PR-20 — vision OCR find/invoke + routing fallback."""

from __future__ import annotations

from typing import Any

import pytest

from vdisplay.control.models import ControlBounds
from vdisplay.control.policy import evaluate_provider_routing
from vdisplay.control.providers.vision import VisionStubProvider
from vdisplay.control.selector import ControlSelector
from vdisplay.control.vision_ocr import OcrTextBox, match_selector_boxes, ocr_find_selector


def _fake_png() -> bytes:
    from PIL import Image
    import io

    image = Image.new("RGB", (200, 80), color=(255, 255, 255))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def _mock_ocr_boxes(monkeypatch: pytest.MonkeyPatch, boxes: list[OcrTextBox]) -> None:
    monkeypatch.setattr("vdisplay.control.providers.vision.provider.ocr_find_selector", lambda *_a, **_k: (boxes, boxes))
    monkeypatch.setattr("vdisplay.control.providers.vision.provider.ocr_available", lambda: (True, "tesseract ok"))


def test_match_selector_boxes_vision_anchor_fuzzy() -> None:
    boxes = [
        OcrTextBox("Submit Order", ControlBounds(x=10, y=20, width=80, height=18), 0.92),
        OcrTextBox("Cancel", ControlBounds(x=10, y=50, width=50, height=18), 0.88),
    ]
    matched = match_selector_boxes(boxes, ControlSelector(vision_anchor="submit"))
    assert len(matched) == 1
    assert "submit" in matched[0].text.lower()


def test_match_selector_boxes_text_exact() -> None:
    boxes = [
        OcrTextBox("OK", ControlBounds(x=1, y=2, width=20, height=10), 0.9),
        OcrTextBox("Cancel", ControlBounds(x=30, y=2, width=40, height=10), 0.9),
    ]
    matched = match_selector_boxes(boxes, ControlSelector(text="OK"))
    assert len(matched) == 1
    assert matched[0].text == "OK"


def test_vision_find_ocr_returns_bounds(monkeypatch: pytest.MonkeyPatch) -> None:
    boxes = [
        OcrTextBox("Play", ControlBounds(x=40, y=60, width=50, height=20), 0.95),
    ]
    _mock_ocr_boxes(monkeypatch, boxes)
    monkeypatch.setattr(
        VisionStubProvider,
        "_capture_png",
        lambda self, **kwargs: (_fake_png(), {"method": "test"}),
    )

    provider = VisionStubProvider()
    nodes = provider.find(ControlSelector(vision_anchor="Play"))
    assert len(nodes) == 1
    assert nodes[0].bounds.width == 50
    assert nodes[0].state.get("ocr") is True


def test_vision_invoke_clicks_ocr_center(monkeypatch: pytest.MonkeyPatch) -> None:
    boxes = [
        OcrTextBox("Go", ControlBounds(x=100, y=200, width=40, height=20), 0.91),
    ]
    _mock_ocr_boxes(monkeypatch, boxes)
    monkeypatch.setattr(
        VisionStubProvider,
        "_capture_png",
        lambda self, **kwargs: (_fake_png(), {}),
    )
    clicked: list[tuple[int, int]] = []

    provider = VisionStubProvider(pointer_click=lambda x, y: clicked.append((x, y)))
    nodes = provider.find(ControlSelector(vision_anchor="Go"))
    result = provider.invoke(nodes[0].id)
    assert result["ok"] is True
    assert clicked == [(120, 210)]


def test_vision_set_value_types_after_click(monkeypatch: pytest.MonkeyPatch) -> None:
    boxes = [OcrTextBox("Name", ControlBounds(x=5, y=5, width=60, height=16), 0.9)]
    _mock_ocr_boxes(monkeypatch, boxes)
    monkeypatch.setattr(VisionStubProvider, "_capture_png", lambda self, **kwargs: (_fake_png(), {}))
    typed: list[str] = []
    provider = VisionStubProvider(
        pointer_click=lambda _x, _y: None,
        pointer_type=lambda text: typed.append(text),
    )
    nodes = provider.find(ControlSelector(text_contains="Name"))
    result = provider.set_value(nodes[0].id, "Alice")
    assert result["ok"] is True
    assert typed == ["Alice"]


def test_vision_ocr_miss_returns_empty_find(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "vdisplay.control.providers.vision.provider.ocr_find_selector",
        lambda *_a, **_k: ([], []),
    )
    monkeypatch.setattr(
        "vdisplay.control.providers.vision.provider.ocr_available",
        lambda: (True, "ok"),
    )
    monkeypatch.setattr(
        VisionStubProvider,
        "_capture_png",
        lambda self, **kwargs: (_fake_png(), {}),
    )
    provider = VisionStubProvider()
    assert provider.find(ControlSelector(vision_anchor="missing")) == []


def test_vision_only_surface_still_routes_x11_when_ocr_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.control.descriptors import HostEnvironmentKind, PlatformProfile

    monkeypatch.setattr("vdisplay.control.scoring._atspi_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._uia_ready", lambda: (False, "n/a"))
    monkeypatch.setattr("vdisplay.control.scoring._ax_ready", lambda: (False, "n/a"))
    monkeypatch.setattr("vdisplay.control.scoring._browser_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._xdotool_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._terminal_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._vision_ready", lambda: (True, "vision OCR"))
    monkeypatch.setattr(
        "vdisplay.control.scoring._browser_session_ready",
        lambda _sid: (True, "ok"),
    )
    monkeypatch.setattr(
        "vdisplay.control.scoring._terminal_session_ready",
        lambda _sid: (True, "ok"),
    )
    monkeypatch.setattr(
        "vdisplay.control.descriptors.detect_platform_profile",
        lambda **kwargs: PlatformProfile(
            os_family="linux",
            display_stack="x11",
            host_environment=HostEnvironmentKind.LINUX_X11,
        ),
    )

    decision = evaluate_provider_routing(
        backend="auto",
        selector=ControlSelector(vision_anchor="play-btn"),
    )
    assert decision.selected_provider == "x11"


def test_ocr_find_selector_with_mocked_ocr_png(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_boxes = [
        OcrTextBox("hello", ControlBounds(x=0, y=0, width=10, height=10), 0.99),
    ]
    monkeypatch.setattr("vdisplay.control.vision_ocr.ocr_png", lambda *_a, **_k: fake_boxes)
    _all, matched = ocr_find_selector(_fake_png(), ControlSelector(text_contains="hel"))
    assert len(matched) == 1
