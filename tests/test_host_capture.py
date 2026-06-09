from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from vdisplay.capture.host import capture_host_png
from vdisplay.exceptions import VDisplayError


def test_capture_host_png_prefers_mirror(monkeypatch: pytest.MonkeyPatch) -> None:
    png = b"\x89PNG\r\n\x1a\n" + b"x" * 64

    monkeypatch.setattr(
        "vdisplay.capture.host.list_monitors",
        lambda _display: [
            {"name": "DP-1", "primary": True, "x": 0, "y": 0, "width": 100, "height": 80},
            {"name": "DP-2", "primary": False, "x": 100, "y": 0, "width": 100, "height": 80},
        ],
    )
    monkeypatch.setattr("vdisplay.capture.host.resolve_host_display", lambda _d: ":0")
    monkeypatch.setattr("vdisplay.capture.host._wayland_host_session", lambda _d: False)
    monkeypatch.setattr("vdisplay.capture.host.is_blank_png", lambda _data: False)
    monkeypatch.setattr(
        "vdisplay.capture.host.capture_display_png",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(VDisplayError("forced mirror fallback")),
    )

    session = MagicMock()
    session.screenshot_bytes.return_value = png
    session.info.return_value = {"target": "DP-2", "kind": "mirror"}

    mirror_cls = MagicMock()
    mirror_cls.create.return_value = session
    with patch("vdisplay.api.MirrorSession", mirror_cls):
        data, meta = capture_host_png(monitor=1)

    assert data == png
    assert meta["method"] == "mirror"
    mirror_cls.create.assert_called_once()
    session.start.assert_called_once()
    session.stop.assert_called_once()
