from __future__ import annotations

import io

import pytest

from vdisplay.capture.linux_xwd import PNG_SIGNATURE, _crop_png, capture_display_png, is_blank_png


def _make_png(width: int, height: int, color: tuple[int, int, int]) -> bytes:
    from PIL import Image

    image = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def test_crop_png_extracts_region() -> None:
    full = _make_png(100, 80, (255, 0, 0))
    cropped = _crop_png(full, (10, 20, 30, 40))
    assert cropped[:8] == PNG_SIGNATURE
    from PIL import Image

    image = Image.open(io.BytesIO(cropped))
    assert image.size == (30, 40)


def test_capture_display_png_region_uses_provider_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    full = _make_png(200, 100, (0, 128, 255))
    from vdisplay.capture.providers.base import ProviderResult

    monkeypatch.setattr(
        "vdisplay.capture.providers.engine._try_providers",
        lambda providers, display, region=None: ProviderResult(
            png=full,
            provider="stub",
        ),
    )

    png = capture_display_png(":0", region=(50, 10, 60, 40))
    assert png == full


def test_is_blank_png_detects_black() -> None:
    black = _make_png(32, 32, (0, 0, 0))
    assert is_blank_png(black) is True
    colored = _make_png(32, 32, (20, 40, 200))
    assert is_blank_png(colored) is False
