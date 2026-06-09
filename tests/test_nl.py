from __future__ import annotations

from vdisplay.nl import (
    describe_output_nl,
    describe_window_nl,
    enrich_outputs_nl,
    window_center_on_output,
)


def test_describe_window_nl_application() -> None:
    info = {
        "app_label": "Toolbox",
        "title": "Toolbox",
        "type": "application",
        "width": 880,
        "height": 1326,
        "x": 4470,
        "y": 298,
        "process_name": "jetbrains-toolb",
        "wm_class": "jetbrains-toolbox",
        "is_internal": False,
    }
    nl = describe_window_nl(info)
    assert "Toolbox" in nl
    assert "880×1326" in nl
    assert "jetbrains-toolb" in nl


def test_describe_output_nl_with_apps() -> None:
    output = {
        "name": "DP-2",
        "primary": True,
        "connected": True,
        "width": 4320,
        "height": 7680,
        "rotation": "left",
        "rotation_degrees": 90,
    }
    windows = [{"app_label": "Toolbox"}, {"app_label": "Firefox"}]
    nl = describe_output_nl(output, windows)
    assert "Primary monitor DP-2" in nl
    assert "Toolbox" in nl
    assert "Firefox" in nl


def test_describe_output_nl_empty_monitor() -> None:
    output = {"name": "HDMI-1", "connected": True, "width": 1920, "height": 1080}
    nl = describe_output_nl(output, [])
    assert "No visible application windows" in nl


def test_window_center_on_output() -> None:
    window = {"x": 4470, "y": 298, "width": 880, "height": 1326}
    output = {"x": 4096, "y": 0, "width": 4320, "height": 7680}
    assert window_center_on_output(window, output)


def test_enrich_outputs_nl_adds_field() -> None:
    outputs = [{"name": "DP-1", "x": 0, "y": 0, "width": 1920, "height": 1080, "connected": True}]
    windows = [
        {
            "app_label": "Terminal",
            "x": 100,
            "y": 100,
            "width": 800,
            "height": 600,
        }
    ]
    enriched = enrich_outputs_nl(outputs, windows)
    assert enriched[0]["nl"]
    assert "Terminal" in enriched[0]["nl"]
