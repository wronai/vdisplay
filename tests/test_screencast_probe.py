"""Screencast probe CLI/service tests."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from vdisplay.application.services.screencast_cli import probe_screencast_capture
from vdisplay.exceptions import VDisplayError


def _png() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"x" * 128


def test_probe_requires_keeper(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(runtime))
    with pytest.raises(VDisplayError, match="keeper not running"):
        probe_screencast_capture(source="DP-1")


def test_probe_keeper_capture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(runtime))
    state = {
        "pid": os.getpid(),
        "session_path": "/org/freedesktop/portal/desktop/session/test/probe",
        "socket_path": str(runtime / "vdisplay-screencast.sock"),
        "node_ids": [136, 133, 116],
        "streams": [
            {"node_id": 136, "properties": {"id": "2", "position": [0, 652], "size": [2048, 1280]}},
            {"node_id": 133, "properties": {"id": "1", "position": [0, 1932], "size": [2048, 1280]}},
            {"node_id": 116, "properties": {"id": "0", "position": [2048, 0], "size": [2160, 3840]}},
        ],
    }
    (runtime / "vdisplay-screencast-keeper.json").write_text(json.dumps(state), encoding="utf-8")

    monkeypatch.setattr(
        "vdisplay.application.services.screencast_cli.read_keeper_state",
        lambda: state,
    )
    monkeypatch.setattr(
        "vdisplay.application.services.screencast_cli.keeper_capture_ready",
        lambda _state=None, **kwargs: True,
    )
    monkeypatch.setattr(
        "vdisplay.capture.screencast_keeper.request_keeper_capture",
        lambda **kwargs: _png(),
    )
    monkeypatch.setattr(
        "vdisplay.capture.host.list_monitors",
        lambda display: [{"name": "DP-1", "x": 0, "y": 652, "width": 2048, "height": 1280}],
    )
    monkeypatch.setattr(
        "vdisplay.capture.host.resolve_host_display",
        lambda display: ":0",
    )

    payload = probe_screencast_capture(source="DP-1")
    assert payload["ok"] is True
    assert payload["via"] == "keeper"
    assert payload["target_object"] == "2"
    assert payload["bytes"] > 0
