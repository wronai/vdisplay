from __future__ import annotations

import io

import pytest
from PIL import Image

from vdisplay.capture.host import capture_all_monitors
from vdisplay.capture.portal_screencast import PortalScreenCastSession
from vdisplay.capture.screencast_stream_matching import assign_screencast_streams_to_monitors


def _png(color: tuple[int, int, int]) -> bytes:
    image = Image.new("RGB", (64, 48), color)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def test_assign_streams_portrait_and_landscape() -> None:
    class Session:
        streams = [
            {"node_id": 74, "properties": {"id": "0", "position": [2048, 0], "size": [2160, 3840]}},
            {"node_id": 100, "properties": {"id": "2", "position": [0, 652], "size": [2048, 1280]}},
            {"node_id": 86, "properties": {"id": "1", "position": [0, 1932], "size": [2048, 1280]}},
        ]
        node_ids = [74, 100, 86]

    monitors = [
        {"name": "DP-1", "x": 0, "y": 1304, "width": 4096, "height": 2560, "rotation": "normal"},
        {"name": "HDMI-1", "x": 0, "y": 3864, "width": 4096, "height": 2560, "rotation": "normal"},
        {"name": "DP-2", "x": 4096, "y": 0, "width": 4320, "height": 7680, "rotation": "left"},
    ]
    mapping = assign_screencast_streams_to_monitors(Session(), monitors)
    assert len(mapping) == 3
    assert len(set(mapping.values())) == 3
    assert mapping["DP-2"] == 0
    assert mapping["DP-1"] == 1
    assert mapping["HDMI-1"] == 2


def test_capture_all_monitors_multi_stream_uses_per_stream_png(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    colors = [(40, 120, 200), (200, 80, 20), (120, 200, 80)]
    session = PortalScreenCastSession()
    session.active = True
    session.session_path = "/org/freedesktop/portal/desktop/session/test/vdisplay_screencast"
    session.node_ids = [74, 100, 86]
    session.streams = [
        {"node_id": 74, "properties": {"id": "0", "position": [2048, 0], "size": [2160, 3840]}},
        {"node_id": 100, "properties": {"id": "2", "position": [0, 652], "size": [2048, 1280]}},
        {"node_id": 86, "properties": {"id": "1", "position": [0, 1932], "size": [2048, 1280]}},
    ]

    def capture_png(*, node_index: int = 0) -> bytes:
        return _png(colors[node_index % len(colors)])

    session.capture_png = lambda **kwargs: capture_png(**kwargs)  # type: ignore[method-assign]

    monitors = [
        {"name": "DP-1", "x": 0, "y": 1304, "width": 4096, "height": 2560},
        {"name": "HDMI-1", "x": 0, "y": 3864, "width": 4096, "height": 2560},
        {"name": "DP-2", "x": 4096, "y": 0, "width": 4320, "height": 7680, "rotation": "left"},
    ]
    monkeypatch.setattr("vdisplay.capture.host.list_monitors", lambda display: monitors)

    bulk = capture_all_monitors(display=":0", out_dir=tmp_path, screencast_session=session)
    assert bulk["count"] == 3
    payloads = {item["monitor_name"]: item for item in bulk["captures"]}
    assert payloads["DP-1"]["method"] == "portal-screencast+stream"
    assert payloads["HDMI-1"]["method"] == "portal-screencast+stream"
    assert payloads["DP-2"]["method"] == "portal-screencast+stream"
    assert payloads["DP-1"]["path"] != payloads["HDMI-1"]["path"]
