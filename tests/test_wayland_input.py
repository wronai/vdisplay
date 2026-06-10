"""Wayland ydotool input + screenshot coordinate mapping."""

from __future__ import annotations

import pytest

from vdisplay.input.coords import global_pointer_coords
from vdisplay.input.resolve import resolve_pointer_input


def test_enrich_screencast_stream_meta_from_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.control.screenshot_verify import enrich_screencast_stream_meta

    monkeypatch.setattr(
        "vdisplay.control.screenshot_verify._resolve_screencast_stream_region",
        lambda: {"x": 0, "y": 1932, "width": 2048, "height": 1280},
    )
    meta = enrich_screencast_stream_meta(
        {"width": 2560, "height": 1600, "screencast_full_frame": True, "method": "portal-screencast"}
    )
    assert meta["screencast_stream"] is True
    assert meta["region"] == {"x": 0, "y": 1932, "width": 2048, "height": 1280}


def test_global_pointer_coords_screencast_stream() -> None:
    gx, gy, mapping = global_pointer_coords(
        100,
        50,
        {
            "width": 2560,
            "height": 1600,
            "screencast_stream": True,
            "region": {"x": 0, "y": 1932, "width": 2048, "height": 1280},
        },
    )
    assert mapping["mapping"] == "screencast-stream"
    assert gx == int(100 * (2048 / 2560))
    assert gy == 1932 + int(50 * (1280 / 1600))


def test_global_pointer_coords_region_scale() -> None:
    gx, gy, mapping = global_pointer_coords(
        100,
        50,
        {
            "width": 2560,
            "height": 1600,
            "region": {"x": 4096, "y": 0, "width": 4320, "height": 7680},
        },
    )
    assert mapping["mapping"] == "region"
    assert gx == 4096 + int(100 * (4320 / 2560))
    assert gy == 0 + int(50 * (7680 / 1600))


def test_global_pointer_coords_monitor_1to1_on_rotation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "vdisplay.input.coords._monitor_by_name",
        lambda *_a, **_k: {"name": "DP-2", "x": 4096, "y": 0, "width": 4320, "height": 7680},
    )
    gx, gy, mapping = global_pointer_coords(
        100,
        50,
        {"width": 2560, "height": 1600, "source": "DP-2"},
    )
    assert mapping["mapping"] == "monitor-1:1"
    assert gx == 4096 + 100
    assert gy == 50


def test_global_pointer_coords_local_fallback() -> None:
    gx, gy, mapping = global_pointer_coords(10, 20, {})
    assert (gx, gy) == (10, 20)
    assert mapping["mapping"] == "local"


def test_resolve_pointer_input_prefers_ydotool_on_wayland(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("vdisplay.input.resolve._is_wayland_session", lambda: True)
    monkeypatch.setattr(
        "vdisplay.input.resolve.LinuxYdotoolInput.available",
        staticmethod(lambda: (True, "ok")),
    )
    _inp, method = resolve_pointer_input()
    assert method == "ydotool"


def test_resolve_pointer_input_xdotool_on_x11(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("vdisplay.input.resolve._is_wayland_session", lambda: False)
    _inp, method = resolve_pointer_input(display=":0")
    assert method == "xdotool"


def test_vision_pointer_click_uses_ydotool_on_wayland(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.control.models import ControlBounds
    from vdisplay.control.providers.vision import VisionStubProvider

    moves: list[tuple[int, int]] = []
    clicks: list[int] = []

    class FakeYdotool:
        def move(self, x: int, y: int) -> None:
            moves.append((x, y))

        def click(self, button: int = 1) -> None:
            clicks.append(button)

        def type_text(self, text: str) -> None:
            pass

    monkeypatch.setattr("vdisplay.input.resolve._is_wayland_session", lambda: True)
    monkeypatch.setattr(
        "vdisplay.input.resolve.LinuxYdotoolInput.available",
        staticmethod(lambda: (True, "ok")),
    )
    monkeypatch.setattr("vdisplay.input.resolve.LinuxYdotoolInput", FakeYdotool)
    monkeypatch.setattr(
        "vdisplay.input.coords.global_pointer_coords",
        lambda *_a, **_k: (5000, 1400, {"mapping": "region"}),
    )
    monkeypatch.setattr(
        "vdisplay.input.resolve.resolve_pointer_input",
        lambda **_k: (FakeYdotool(), "ydotool"),
    )

    provider = VisionStubProvider()
    result = provider._pointer_click_at(
        ControlBounds(x=1700, y=1420, width=40, height=20),
        capture_meta={"width": 2560, "height": 1600, "region": {"x": 4096, "y": 0, "width": 4320, "height": 7680}},
    )
    assert result["ok"] is True
    assert result["method"] == "ydotool"
    assert moves == [(5000, 1400)]
    assert clicks == [1]
