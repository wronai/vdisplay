"""PR-22 — vision template matching find/invoke."""

from __future__ import annotations

import io

import pytest

from vdisplay.control.models import ControlBounds
from vdisplay.control.providers.vision import VisionStubProvider
from vdisplay.control.selector import ControlSelector
from vdisplay.control.vision_template import match_template, template_available


def _template_png() -> bytes:
    from PIL import Image

    image = Image.new("RGB", (20, 20))
    for x in range(20):
        for y in range(20):
            image.putpixel((x, y), (x * 12, y * 12, 40 + x))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def _screen_with_template_at(x: int, y: int) -> bytes:
    from PIL import Image

    screen = Image.new("RGB", (120, 120), color=(240, 240, 240))
    template = Image.open(io.BytesIO(_template_png()))
    screen.paste(template, (x, y))
    buf = io.BytesIO()
    screen.save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.skipif(not template_available()[0], reason="opencv not installed")
def test_match_template_finds_embedded_pattern() -> None:
    screen = _screen_with_template_at(35, 45)
    matches = match_template(screen, _template_png(), threshold=0.95)
    assert matches
    best = matches[0]
    assert best.bounds.x == 35
    assert best.bounds.y == 45
    assert best.confidence >= 0.95


@pytest.mark.skipif(not template_available()[0], reason="opencv not installed")
def test_vision_find_template_returns_bounds(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    screen = _screen_with_template_at(10, 15)
    template_path = tmp_path / "btn.png"
    template_path.write_bytes(_template_png())
    monkeypatch.setattr(
        VisionStubProvider,
        "_capture_png",
        lambda self, **kwargs: (screen, {"method": "test"}),
    )

    provider = VisionStubProvider()
    nodes = provider.find(ControlSelector(vision_template=str(template_path)))
    assert nodes
    hit = next(n for n in nodes if n.bounds.x == 10 and n.bounds.y == 15)
    assert hit.state.get("template") is True


@pytest.mark.skipif(not template_available()[0], reason="opencv not installed")
def test_template_match_threshold_tuning() -> None:
    screen = _screen_with_template_at(35, 45)
    low = match_template(screen, _template_png(), threshold=0.5)
    high = match_template(screen, _template_png(), threshold=0.99)
    assert len(low) >= len(high)
    assert high
    assert high[0].bounds.x == 35


@pytest.mark.skipif(not template_available()[0], reason="opencv not installed")
def test_vision_invoke_clicks_template_center(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    screen = _screen_with_template_at(30, 40)
    template_path = tmp_path / "btn.png"
    template_path.write_bytes(_template_png())
    monkeypatch.setattr(
        VisionStubProvider,
        "_capture_png",
        lambda self, **kwargs: (screen, {}),
    )
    clicked: list[tuple[int, int]] = []
    provider = VisionStubProvider(pointer_click=lambda x, y: clicked.append((x, y)))
    nodes = provider.find(ControlSelector(vision_template=str(template_path)))
    result = provider.invoke(nodes[0].id)
    assert result["ok"] is True
    assert clicked == [(40, 50)]
