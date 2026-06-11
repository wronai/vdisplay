from __future__ import annotations

from vdisplay.monitor_geometry import parse_geometry_mm
from vdisplay.discovery import _merge_output_metadata


def test_parse_geometry_mm_from_xrandr_listmonitors() -> None:
    parsed = parse_geometry_mm("4096/610x2560/350+0+1304")
    assert parsed["width_px"] == 4096
    assert parsed["height_px"] == 2560
    assert parsed["width_mm"] == 610
    assert parsed["height_mm"] == 350
    assert parsed["geometry_x"] == 0
    assert parsed["geometry_y"] == 1304
    assert parsed["diagonal_in"] == 27.7


def test_merge_output_metadata_includes_physical_size() -> None:
    monitors = [
        {
            "name": "DP-1",
            "geometry": "4096/610x2560/350+0+1304",
            "monitor_index": 0,
            "label": "DP-1",
            "connected": True,
            "primary": False,
        }
    ]
    query = {
        "DP-1": {
            "connected": True,
            "primary": False,
            "geometry": "4096x2560+0+1304",
            "width": 4096,
            "height": 2560,
            "x": 0,
            "y": 1304,
            "rotation": "normal",
            "rotation_degrees": 0,
        }
    }
    merged = _merge_output_metadata(monitors, query)
    assert merged[0]["width_mm"] == 610
    assert merged[0]["height_mm"] == 350
    assert merged[0]["diagonal_in"] == 27.7
