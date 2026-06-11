"""Rotation-aware pointer coordinate mapping."""

from __future__ import annotations

import pytest

from vdisplay.input.coords import global_pointer_coords


def test_global_pointer_coords_rotated_left_aspect_mismatch() -> None:
    gx, gy, mapping = global_pointer_coords(
        100,
        50,
        {
            "width": 2560,
            "height": 1600,
            "rotation": "left",
            "region": {"x": 4096, "y": 0, "width": 4320, "height": 7680},
        },
    )
    assert "rotation-left" in mapping["mapping"]
    assert gx > 4096
    assert gy >= 0


def test_global_pointer_coords_monitor_1to1_on_normal_rotation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "vdisplay.capture.coordinate_map._monitor_by_name",
        lambda *_a, **_k: {"name": "DP-1", "x": 0, "y": 0, "width": 1920, "height": 1080, "rotation": "normal"},
    )
    gx, gy, mapping = global_pointer_coords(
        100,
        50,
        {"width": 1920, "height": 1080, "source": "DP-1"},
    )
    assert mapping["mapping"] == "monitor"
    assert gx == 100
    assert gy == 50


def test_global_region_to_capture_local_screencast_stream() -> None:
    from vdisplay.input.coords import global_point_to_capture_local, global_region_to_capture_local

    meta = {
        "width": 2560,
        "height": 1600,
        "screencast_full_frame": True,
        "screencast_stream": True,
        "region": {"x": 0, "y": 1932, "width": 2048, "height": 1280},
    }
    local = global_region_to_capture_local((1951, 2373, 744, 72), meta)
    assert local is not None
    lx, ly, lw, lh = local
    assert lx < 2560
    assert ly < 1600
    assert lw > 0
    assert lh > 0
    point = global_point_to_capture_local(1500, 2400, meta)
    assert 0 <= point[0] < 2560
    assert 0 <= point[1] < 1600


def test_global_point_roundtrip_screencast_stream() -> None:
    meta = {
        "width": 2560,
        "height": 1600,
        "screencast_full_frame": True,
        "screencast_stream": True,
        "region": {"x": 0, "y": 1932, "width": 2048, "height": 1280},
    }
    gx, gy, mapping = global_pointer_coords(1200, 800, meta)
    assert mapping["mapping"] == "screencast-stream"
    from vdisplay.input.coords import global_point_to_capture_local

    lx, ly = global_point_to_capture_local(gx, gy, meta)
    assert abs(lx - 1200) <= 2
    assert abs(ly - 800) <= 2
