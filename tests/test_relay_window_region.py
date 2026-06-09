from __future__ import annotations

import io

import pytest

from vdisplay.exceptions import VDisplayError


def _make_png(width: int, height: int, color: tuple[int, int, int]) -> bytes:
    from PIL import Image

    image = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def test_relay_screenshot_crops_window_region(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    full_png = _make_png(200, 100, (0, 0, 0))
    window = {
        "window_id": "0xabc",
        "title": "Test App",
        "app_label": "test-app",
        "pid": 4242,
        "x": 40,
        "y": 10,
        "width": 60,
        "height": 30,
    }

    monkeypatch.setattr(
        "vdisplay.capture.host.resolve_window_region",
        lambda display, **kwargs: ((40, 10, 60, 30), {"window_id": "0xabc", "title": "Test App"}),
    )

    captured: dict[str, object] = {}

    def fake_capture_host_to_file(path, **kwargs):
        captured.update(kwargs)
        out = tmp_path / "relay.png"
        out.write_bytes(_make_png(60, 30, (255, 0, 0)))
        return {
            "path": str(out),
            "bytes": out.stat().st_size,
            "method": "portal-screencast+crop",
            "region": {"x": 40, "y": 10, "width": 60, "height": 30},
        }

    monkeypatch.setattr("vdisplay.capture.host.capture_host_to_file", fake_capture_host_to_file)
    monkeypatch.setattr("vdisplay.discovery.resolve_host_display", lambda display: ":0")

    from vdisplay.application.services.session import relay_screenshot

    out = tmp_path / "window.png"
    meta = relay_screenshot(str(out), match_title="Test App")
    assert meta["mode"] == "relay"
    assert meta["relay_window"]["window_id"] == "0xabc"
    assert captured["region"] == (40, 10, 60, 30)


def test_resolve_window_region_requires_match(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("vdisplay.windows.find_windows", lambda display, **kwargs: [])
    monkeypatch.setattr("vdisplay.windows.pick_best_window", lambda matches: None)

    from vdisplay.capture.host import resolve_window_region

    with pytest.raises(VDisplayError, match="no window matched"):
        resolve_window_region(":0", match_title="Missing")
