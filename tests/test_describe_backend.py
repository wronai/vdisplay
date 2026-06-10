"""Describe backend selection tests."""

from __future__ import annotations

import pytest


def test_describe_backend_prefers_imgl(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    png = tmp_path / "screen.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)

    monkeypatch.setenv("VDISPLAY_DESCRIBE_BACKEND", "imgl")
    monkeypatch.setattr(
        "vdisplay.application.services.img2nl_enrich._describe_via_imgl",
        lambda path, locale=None: {
            "ok": True,
            "text": "Screen with windows: Toolbox.",
            "locale": "pl",
            "scene_class": "imgl_scene",
            "source": "imgl",
        },
    )

    from vdisplay.application.services import img2nl_enrich

    result = img2nl_enrich.describe_screenshot_image(png)
    assert result["ok"] is True
    assert result["source"] == "imgl"
