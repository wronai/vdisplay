"""Tests for vdisplay hmi watch."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from vdisplay.cli import build_parser
from vdisplay.hmi.keyboard import KeyboardWatcher, _decode_char, _event_device_paths
from vdisplay.hmi.mouse import MouseWatcher, _mouse_device_paths
from vdisplay.hmi.pointer import PointerSample, monitor_at, sample_pointer
from vdisplay.hmi.watch import run_hmi_watch


def test_parser_has_hmi_watch() -> None:
    parser = build_parser()
    kinds = parser._subparsers._group_actions[0].choices  # type: ignore[index]
    assert "hmi" in kinds
    hmi = kinds["hmi"]
    actions = hmi._subparsers._group_actions[0].choices  # type: ignore[index]
    assert "watch" in actions


def test_monitor_at_finds_output() -> None:
    monitors = [
        {"name": "DP-1", "x": 0, "y": 0, "width": 1920, "height": 1080},
        {"name": "DP-2", "x": 4096, "y": 0, "width": 4320, "height": 7680},
    ]

    def fake_list(_display=None):
        return monitors

    import vdisplay.hmi.pointer as pointer_mod

    original = pointer_mod.list_monitors
    pointer_mod.list_monitors = fake_list  # type: ignore[assignment]
    try:
        hit = monitor_at(5000, 100, display=":0")
        assert hit is not None
        assert hit["name"] == "DP-2"
    finally:
        pointer_mod.list_monitors = original


def test_decode_char_shift() -> None:
    assert _decode_char(20, shift=False) == "t"
    assert _decode_char(20, shift=True) == "T"


def test_keyboard_watcher_emits_typed_chars() -> None:
    watcher = KeyboardWatcher()
    watcher._handle_key(20, 1)  # t
    watcher._handle_key(18, 1)  # e
    watcher._handle_key(20, 1)  # t
    assert watcher.typed_buffer == "tet"


def test_mouse_watcher_tracks_relative_motion() -> None:
    mouse = MouseWatcher()
    mouse.seed(100, 200)
    mouse._apply_rel(5, -3)
    assert mouse.position == (105, 197)


def test_sample_pointer_prefers_evdev_on_wayland(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setattr("vdisplay.hmi.pointer.probe_xdotool", lambda **kwargs: (1, 2, "9"))
    monkeypatch.setattr("vdisplay.hmi.pointer.probe_gtk_subprocess", lambda **kwargs: (3, 4))

    history: dict[str, list[tuple[int, int]]] = {}
    sample = sample_pointer(evdev_xy=(500, 600), source_history=history, use_gtk=False)
    assert sample.primary == "evdev"
    assert sample.x == 500
    assert sample.y == 600


def test_sample_pointer_marks_stale_xdotool(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setattr("vdisplay.hmi.pointer.probe_xdotool", lambda **kwargs: (1, 2, "9"))
    history = {"xdotool": [(1, 2)] * 8}
    sample = sample_pointer(evdev_xy=(10, 20), source_history=history, use_gtk=False)
    assert "xdotool" in sample.stale_sources


def test_run_hmi_watch_jsonl(monkeypatch: pytest.MonkeyPatch) -> None:
    sample = PointerSample(x=100, y=200, sources={"evdev": (100, 200)}, primary="evdev", monitor={"name": "DP-1"})

    monkeypatch.setattr("vdisplay.hmi.watch.sample_pointer", lambda **kwargs: sample)
    monkeypatch.setattr("vdisplay.hmi.watch.KeyboardWatcher", lambda: type("K", (), {"start": lambda s: None, "stop": lambda s: None, "drain": lambda s: [], "typed_buffer": ""})())
    monkeypatch.setattr("vdisplay.hmi.watch.MouseWatcher", lambda: type("M", (), {"start": lambda s: None, "stop": lambda s: None, "drain": lambda s: [], "position": None, "seed": lambda s, x, y: None, "move_count": 0})())
    monkeypatch.setattr("vdisplay.hmi.watch._seed_mouse", lambda *a, **k: None)

    buf = io.StringIO()
    rc = run_hmi_watch(interval=0.05, keyboard=False, mouse=False, jsonl=True, stream=buf, stop_after=0.06)
    assert rc == 0
    lines = [json.loads(line) for line in buf.getvalue().splitlines() if line.strip()]
    assert lines[0]["kind"] == "pointer"
    assert lines[0]["primary"] == "evdev"


def test_event_device_paths_parses_proc_input(tmp_path) -> None:
    devices = tmp_path / "devices"
    devices.write_text(
        'N: Name="Test keyboard"\n'
        "H: Handlers=kbd event3 \n\n"
        'N: Name="Mouse"\n'
        "H: Handlers=mouse0 event4 \n",
        encoding="utf-8",
    )
    assert _event_device_paths(devices_path=devices) == [Path("/dev/input/event3")]
    assert _mouse_device_paths(devices_path=devices) == [Path("/dev/input/event4")]
