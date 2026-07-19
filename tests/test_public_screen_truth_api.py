"""Contract tests for screen-truth helpers consumed by external orchestrators."""

from __future__ import annotations

from types import SimpleNamespace

from vdisplay.capture import (
    PortalScreenCastSession,
    get_active_screencast,
    reset_screencast_consent,
    resolve_multi_stream_region,
    start_screencast_session,
    stop_screencast_session,
)
from vdisplay.input import monitor_by_name
from vdisplay.integrations import build_imgl_layers


def test_resolve_multi_stream_region_is_public_and_canonical() -> None:
    session = SimpleNamespace(
        streams=[
            {
                "properties": {
                    "position": [120, 40],
                    "size": [800, 600],
                }
            }
        ]
    )

    assert resolve_multi_stream_region(session, 0, None) == {
        "x": 120,
        "y": 40,
        "width": 800,
        "height": 600,
    }


def test_monitor_by_name_is_public(monkeypatch) -> None:
    monkeypatch.setattr("vdisplay.input.coords.resolve_host_display", lambda display: display or ":0")
    monkeypatch.setattr(
        "vdisplay.input.coords.list_monitors",
        lambda display: [{"name": "DP-2", "display": display, "width": 1920, "height": 1080}],
    )

    assert monitor_by_name(None, "DP-2") == {
        "name": "DP-2",
        "display": ":0",
        "width": 1920,
        "height": 1080,
    }


def test_build_imgl_layers_is_public() -> None:
    layers = build_imgl_layers(
        {
            "ok": True,
            "scene": {
                "elements": [
                    {
                        "id": "send",
                        "type": "button",
                        "text": "Send",
                        "bbox": {"x": 10, "y": 20, "w": 80, "h": 40},
                    }
                ]
            },
        }
    )

    assert layers == [
        {
            "id": "send",
            "kind": "button",
            "text": "Send",
            "bbox": {"x": 10, "y": 20, "w": 80, "h": 40},
            "center": {"x": 50, "y": 40},
            "click_center": {"x": 50, "y": 40},
        }
    ]


def test_screencast_lifecycle_is_public() -> None:
    assert PortalScreenCastSession is not None
    assert callable(get_active_screencast)
    assert callable(start_screencast_session)
    assert callable(stop_screencast_session)
    assert callable(reset_screencast_consent)
