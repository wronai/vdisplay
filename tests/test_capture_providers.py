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


class _StubProvider:
    name = "stub"

    def __init__(self, png: bytes) -> None:
        self._png = png

    def available(self) -> tuple[bool, str]:
        return True, "stub"

    def capture_full(self) -> bytes:
        return self._png

    def capture_region(self, region: tuple[int, int, int, int]) -> bytes:
        return self._png


def test_try_providers_prefers_first_non_blank() -> None:
    from vdisplay.capture.providers.engine import _try_providers

    blank = _make_png(32, 32, (0, 0, 0))
    colored = _make_png(32, 32, (40, 120, 200))
    result = _try_providers([_StubProvider(blank), _StubProvider(colored)], display=":0", region=None)
    assert result.provider == "stub"
    assert result.png == colored


def test_list_capture_providers_includes_drm() -> None:
    from vdisplay.capture.providers.engine import list_capture_providers

    rows = list_capture_providers(":0")
    names = {row["name"] for row in rows}
    assert {"drm", "fbdev", "mss", "x11"}.issubset(names)


def test_x11_provider_region_falls_back_to_crop(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.capture.providers.x11 import X11Provider

    full = b"\x89PNG\r\n\x1a\n" + b"rest"
    monkeypatch.setattr(
        "vdisplay.capture.providers.x11._capture_scrot_png",
        lambda display, region: b"" if region else full,
    )
    monkeypatch.setattr(
        "vdisplay.capture.providers.x11._crop_png",
        lambda data, region: b"\x89PNG\r\n\x1a\n cropped",
    )
    provider = X11Provider(":99")
    assert provider.capture_region((1, 2, 3, 4)) == b"\x89PNG\r\n\x1a\n cropped"
