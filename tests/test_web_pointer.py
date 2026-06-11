"""Tests for web console pointer click mapping."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from vdisplay.application.services.web_pointer import (
    build_monitor_capture_meta,
    pointer_click_at_monitor,
)


def test_build_monitor_capture_meta_uses_monitor_region(tmp_path: Path) -> None:
    png = tmp_path / "DP-1.png"
    png.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        + b"\x00\x00\x07\x80\x00\x00\x04\x38\x08\x02\x00\x00\x00"
        + b"\x00" * 4
        + b"IEND\xaeB`\x82"
    )
    monitor = {"name": "DP-1", "x": 0, "y": 1304, "width": 4096, "height": 2560, "rotation": "normal"}
    meta = build_monitor_capture_meta({}, monitor=monitor, png_path=png)
    assert meta["width"] == 1920
    assert meta["height"] == 1080
    assert meta["region"]["x"] == 0
    assert meta["region"]["y"] == 1304


def test_pointer_click_at_monitor_invokes_input(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    png = tmp_path / "DP-1.png"
    png.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        + b"\x00\x00\x00\x64\x00\x00\x00\x64\x08\x02\x00\x00\x00"
        + b"\x00" * 4
        + b"IEND\xaeB`\x82"
    )
    monkeypatch.setattr(
        "vdisplay.application.services.web_pointer._monitor_by_name",
        lambda *_a, **_k: {"name": "DP-1", "x": 0, "y": 0, "width": 100, "height": 100, "rotation": "normal"},
    )
    monkeypatch.setattr(
        "vdisplay.application.services.web_pointer.global_pointer_coords",
        lambda *_a, **_k: (42, 24, {"mapping": "monitor"}),
    )
    monkeypatch.setattr(
        "vdisplay.application.services.web_pointer.global_point_in_stream_bounds",
        lambda *_a, **_k: True,
    )
    monkeypatch.setattr("vdisplay.application.services.web_pointer.control_pointer_settle_seconds", lambda: 0)

    inp = MagicMock()
    monkeypatch.setattr(
        "vdisplay.application.services.web_pointer.resolve_pointer_input",
        lambda **_k: (inp, "mock-input"),
    )

    result = pointer_click_at_monitor(
        monitor_name="DP-1",
        x=10,
        y=20,
        capture_meta={"width": 100, "height": 100, "source": "DP-1"},
        png_path=png,
    )
    assert result["ok"] is True
    assert result["global_x"] == 42
    inp.move.assert_called_once_with(42, 24)
    inp.click.assert_called_once_with(1)
