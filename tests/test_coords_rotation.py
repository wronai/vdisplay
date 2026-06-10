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
        "vdisplay.input.coords._monitor_by_name",
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
