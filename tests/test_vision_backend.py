"""Vision backend delegation tests."""

from __future__ import annotations

import io

import pytest


def _png(color: tuple[int, int, int]) -> bytes:
    pytest.importorskip("PIL")
    from PIL import Image

    image = Image.new("RGB", (6, 6), color=color)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def test_diff_png_bytes_local_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_VISION_BACKEND", "local")
    from vdisplay.control.screenshot_verify import diff_png_bytes

    result = diff_png_bytes(_png((255, 0, 0)), _png((0, 255, 0)), min_changed_pixels=1)
    assert result["verified"] is True


def test_match_template_local_path(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("cv2")
    monkeypatch.setenv("VDISPLAY_VISION_BACKEND", "local")
    png = _png((10, 10, 10))
    from vdisplay.control.vision_template import match_template

    matches = match_template(png, png, threshold=0.85)
    assert matches
