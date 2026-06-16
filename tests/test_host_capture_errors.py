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


def test_host_capture_error_prefers_electron_manager_agent_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_AGENT_URL", "http://127.0.0.1:8765")
    monkeypatch.setattr(
        "vdisplay.capture.host.electron_share_manager_status",
        lambda: {"browser_bridge": {"agent_url": "http://127.0.0.1:8766"}},
    )
    message = _host_capture_error(
        ":0",
        "DP-1",
        ["electron-share: manager is not sharing"],
    )
    assert "http://127.0.0.1:8766/api/web/browser-bridge?source=DP-1" in message
    assert "http://127.0.0.1:8765/api/web/browser-bridge" not in message


def test_capture_host_png_records_inactive_screencast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setenv("VDISPLAY_ELECTRON_SHARE", "0")
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


def test_capture_host_png_fails_fast_on_stale_electron_frame(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.delenv("VDISPLAY_ELECTRON_SHARE_FALLBACK_ON_ERROR", raising=False)
    monkeypatch.setattr("vdisplay.capture.host.resolve_host_display", lambda _display: ":0")
    monkeypatch.setattr(
        "vdisplay.capture.host.list_monitors",
        lambda _display: [{"name": "HDMI-1", "primary": True, "x": 0, "y": 0, "width": 100, "height": 80}],
    )

    def _stale_electron(*_args, **_kwargs):
        errors = _args[1]
        errors.append("electron-share: stale frame age_ms=6000 exceeds max_age_ms=5000")
        return None

    def _unexpected_screencast(*_args, **_kwargs):
        raise AssertionError("screencast fallback should not run after stale electron-share frame")

    monkeypatch.setattr("vdisplay.capture.host.try_electron_share_capture", _stale_electron)
    monkeypatch.setattr("vdisplay.capture.host.try_screencast_capture", _unexpected_screencast)

    from vdisplay.capture.host import capture_host_png

    with pytest.raises(VDisplayError, match="stale frame age_ms=6000"):
        capture_host_png(source="HDMI-1")
