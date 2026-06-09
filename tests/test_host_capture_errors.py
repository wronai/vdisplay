from __future__ import annotations

import pytest

from vdisplay.capture.host import _host_capture_error
from vdisplay.exceptions import VDisplayError


def test_host_capture_error_mentions_screencast_on_wayland(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    message = _host_capture_error(
        ":0",
        "DP-1",
        ["portal-screencast: no active session (run: vdisplay agent screencast start)", "drm: failed"],
    )
    assert "screencast start" in message
    assert "127.0.0.1:8765" in message


def test_capture_host_png_records_inactive_screencast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setattr(
        "vdisplay.capture.host.list_monitors",
        lambda display: [{"name": "DP-1", "primary": True, "x": 0, "y": 0, "width": 100, "height": 80}],
    )
    monkeypatch.setattr(
        "vdisplay.capture.host.capture_display_png",
        lambda *args, **kwargs: (_ for _ in ()).throw(VDisplayError("driver failed")),
    )
    monkeypatch.setattr("vdisplay.capture.portal_screencast.get_active_screencast", lambda: None)

    from vdisplay.capture.host import capture_host_png

    with pytest.raises(VDisplayError, match="portal-screencast: no active session"):
        capture_host_png(source="DP-1")
