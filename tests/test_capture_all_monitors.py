from __future__ import annotations

import io

import pytest

from vdisplay.capture.portal_screencast import PortalScreenCastSession
from vdisplay.capture.host import capture_all_monitors


def _make_png(width: int, height: int, color: tuple[int, int, int]) -> bytes:
    from PIL import Image

    image = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def test_capture_all_monitors_uses_single_screencast_frame(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    png = _make_png(200, 100, (40, 120, 200))
    session = PortalScreenCastSession()
    session.active = True
    session.session_path = "/org/freedesktop/portal/desktop/session/test/vdisplay_screencast"
    session.node_ids = [42]
    session.capture_png = lambda **kwargs: png  # type: ignore[method-assign]

    monitors = [
        {"name": "DP-2", "x": 100, "y": 0, "width": 50, "height": 100},
        {"name": "DP-1", "x": 0, "y": 0, "width": 200, "height": 100},
        {"name": "HDMI-1", "x": 500, "y": 0, "width": 50, "height": 100},
    ]
    monkeypatch.setattr("vdisplay.capture.host.list_monitors", lambda display: monitors)

    bulk = capture_all_monitors(
        display=":0",
        out_dir=tmp_path,
        screencast_session=session,
    )

    assert bulk["count"] >= 2
    names = {item["monitor_name"] for item in bulk["captures"]}
    assert "DP-1" in names
    assert bulk["warnings"]
