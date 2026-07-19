"""Contract tests for deterministic capture-coordinate compilation."""

from __future__ import annotations

from jsonschema import Draft202012Validator

from vdisplay.capture import (
    COORDINATE_MAP_V1,
    canonicalize_capture_meta,
    compile_capture_coordinate_map,
    coordinate_map_v1_schema,
    resolve_live_capture_meta,
)


def test_canonicalize_capture_meta_uses_ordered_explicit_fallbacks() -> None:
    raw = {
        "source": "DP-2",
        "width": 2048,
        "height": 1280,
        "region": {"x": 0, "y": 0, "width": 2048, "height": 1280},
    }
    fallback = {
        "source": "DP-2",
        "rotation": "left",
        "region": {"x": 0, "y": 1932, "width": 2048, "height": 1280},
        "screencast_stream": True,
    }

    out = canonicalize_capture_meta(
        raw,
        source="DP-2",
        fallback_meta=fallback,
        replace_zero_origin=True,
    )

    assert out["region"]["y"] == 1932
    assert out["rotation"] == "left"
    assert out["screencast_stream"] is True


def test_canonicalize_capture_meta_rejects_wrong_source_fallback() -> None:
    out = canonicalize_capture_meta(
        {
            "source": "DP-1",
            "display_bounds": {"x": 10, "y": 20, "width": 30, "height": 40},
        },
        source="DP-1",
        fallback_meta={
            "source": "DP-2",
            "region": {"x": 99, "y": 99, "width": 100, "height": 100},
        },
        replace_zero_origin=True,
    )

    assert out["region"] == {"x": 10, "y": 20, "width": 30, "height": 40}


def test_coordinate_map_is_stable_and_schema_valid() -> None:
    meta = {
        "source": "HDMI-1",
        "width": 2048,
        "height": 1280,
        "region": {"x": 0, "y": 2560, "width": 4096, "height": 2560},
    }
    first = compile_capture_coordinate_map(meta, source="HDMI-1")
    second = compile_capture_coordinate_map(
        dict(reversed(list(meta.items()))), source="HDMI-1"
    )

    assert first.schema == COORDINATE_MAP_V1
    assert first.coordinate_map_hash == second.coordinate_map_hash
    Draft202012Validator(coordinate_map_v1_schema()).validate(first.to_dict())


def test_coordinate_map_maps_and_clamps_rect() -> None:
    coordinate_map = compile_capture_coordinate_map(
        {
            "source": "HDMI-1",
            "width": 2048,
            "height": 1280,
            "region": {"x": 0, "y": 2560, "width": 4096, "height": 2560},
        },
        source="HDMI-1",
    )

    assert coordinate_map.global_to_local(3216, 3840) == (1608, 640)
    assert coordinate_map.clamp_global_rect(
        (3216, 2550, 880, 1548), min_width=240, min_height=320
    ) == (3216, 2560, 880, 1538)
    local_rect = coordinate_map.global_rect_to_local(
        (3216, 2560, 880, 1538), min_width=120, min_height=160
    )
    assert local_rect is not None
    assert local_rect[0] == 1608
    assert local_rect[2] > 400


def test_coordinate_map_rotation_roundtrip_shape() -> None:
    coordinate_map = compile_capture_coordinate_map(
        {
            "source": "DP-2",
            "width": 2560,
            "height": 1600,
            "rotation": "left",
            "region": {"x": 0, "y": 1932, "width": 2048, "height": 1280},
        },
        source="DP-2",
    )

    local = coordinate_map.global_to_local(1024, 2572, clamp=False)
    assert local is not None
    assert 0 <= local[0] < 2560
    assert 0 <= local[1] < 1600


def test_resolve_live_capture_meta_uses_monitor_snapshot(monkeypatch) -> None:
    monkeypatch.setattr(
        "vdisplay.application.services.discovery.list_monitors_local",
        lambda display=None: {
            "monitors": [
                {
                    "name": "HDMI-1",
                    "x": 0,
                    "y": 2560,
                    "width": 4096,
                    "height": 2560,
                    "rotation": "normal",
                }
            ]
        },
    )
    monkeypatch.setattr(
        "vdisplay.capture.portal_screencast.get_active_screencast",
        lambda: None,
    )

    out = resolve_live_capture_meta("HDMI-1")

    assert out["source"] == "HDMI-1"
    assert out["width"] == 2048
    assert out["height"] == 1280
    assert out["region"] == {
        "x": 0,
        "y": 2560,
        "width": 4096,
        "height": 2560,
    }
