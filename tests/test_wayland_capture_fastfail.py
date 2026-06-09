from __future__ import annotations

import io

import pytest

from vdisplay.capture.portal_screencast import PortalScreenCastSession
from vdisplay.exceptions import VDisplayError


def _black_png() -> bytes:
    from PIL import Image

    image = Image.new("RGB", (32, 32), (0, 0, 0))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def test_blank_screencast_invalidates_session(monkeypatch: pytest.MonkeyPatch) -> None:
    session = PortalScreenCastSession()
    session.active = True
    session.session_path = "/org/freedesktop/portal/desktop/session/test/vdisplay_screencast"
    session.node_ids = [42]
    session.capture_png = lambda **kwargs: _black_png()  # type: ignore[method-assign]
    monkeypatch.setattr("vdisplay.capture.portal_screencast._ACTIVE", session, raising=False)
    monkeypatch.setattr(
        "vdisplay.capture.host._wayland_host_session",
        lambda display: True,
    )
    monkeypatch.setattr(
        "vdisplay.capture.host.list_monitors",
        lambda display: [{"name": "DP-2", "primary": True, "x": 0, "y": 0, "width": 32, "height": 32}],
    )

    from vdisplay.capture.host import capture_host_png

    with pytest.raises(VDisplayError, match="blank frame"):
        capture_host_png(display=":0", source="DP-2")
    assert session.is_ready is False


def test_wayland_host_capture_skips_slow_driver_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("vdisplay.capture.portal_screencast._ACTIVE", None, raising=False)
    monkeypatch.setattr(
        "vdisplay.capture.host._wayland_host_session",
        lambda display: True,
    )
    monkeypatch.setattr(
        "vdisplay.capture.host.list_monitors",
        lambda display: [{"name": "DP-2", "primary": True, "x": 0, "y": 0, "width": 32, "height": 32}],
    )

    def fail_drm(*args, **kwargs):
        raise AssertionError("driver fallback should not run on Wayland")

    monkeypatch.setattr("vdisplay.capture.host.capture_display_png", fail_drm)

    from vdisplay.capture.host import capture_host_png

    with pytest.raises(VDisplayError, match="portal-screencast: no active session"):
        capture_host_png(display=":0", source="DP-2")
