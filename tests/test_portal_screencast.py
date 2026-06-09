from __future__ import annotations

import io

import pytest

from vdisplay.capture.portal_screencast import PortalScreenCastSession, stop_screencast_session
from vdisplay.exceptions import VDisplayError


def _make_png(width: int, height: int, color: tuple[int, int, int]) -> bytes:
    from PIL import Image

    image = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def test_screencast_session_capture_requires_ready() -> None:
    session = PortalScreenCastSession()
    with pytest.raises(VDisplayError, match="not ready"):
        session.capture_png()


def test_host_capture_uses_active_screencast(monkeypatch: pytest.MonkeyPatch) -> None:
    png = _make_png(80, 60, (10, 120, 200))
    session = PortalScreenCastSession()
    session.active = True
    session.node_ids = [42]
    monkeypatch.setattr("vdisplay.capture.portal_screencast._ACTIVE", session, raising=False)
    monkeypatch.setattr(
        "vdisplay.capture.portal_screencast._capture_pipewire_node",
        lambda node_id: png,
    )
    monkeypatch.setattr(
        "vdisplay.capture.host.list_monitors",
        lambda display: [{"name": "DP-1", "primary": True, "x": 0, "y": 0, "width": 80, "height": 60}],
    )

    from vdisplay.capture.host import capture_host_png

    captured, meta = capture_host_png(display=":0", monitor=1, source="DP-1")
    assert captured == png
    assert meta["method"] == "portal-screencast"


def test_agent_screencast_status_endpoint(agent_client) -> None:
    client, _runtime = agent_client
    payload = client.get("/session/screencast/status").json()
    assert payload["ok"] is True
    assert payload["data"]["active"] is False


def test_stop_screencast_when_inactive() -> None:
    stop_screencast_session()
    payload = stop_screencast_session()
    assert payload["ok"] is True
    assert payload["stopped"] is False
