"""Tests for vdisplay hmi watch."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from vdisplay.cli import build_parser
from vdisplay.hmi.context import WindowContextResolver, pick_context_coordinates
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


def test_mouse_watcher_tracks_relative_motion_without_seed() -> None:
    mouse = MouseWatcher()
    mouse._apply_rel(5, -3)
    assert mouse.position == (5, -3)
    assert mouse.relative_only is True


def test_probe_absolute_rejects_gtk_origin_on_wayland(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.hmi.pointer import probe_absolute_pointer

    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setattr("vdisplay.hmi.pointer.probe_gnome_shell_pointer", lambda: None)
    monkeypatch.setattr("vdisplay.hmi.pointer.probe_gtk_subprocess", lambda **kwargs: (0, 0))
    assert probe_absolute_pointer(use_gtk=True) is None


def test_capture_mouse_xy_falls_back_to_xdotool_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.hmi.capture import capture_mouse_xy

    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setattr("vdisplay.hmi.capture.probe_absolute_pointer", lambda **kwargs: None)
    monkeypatch.setattr(
        "vdisplay.hmi.capture.probe_xdotool",
        lambda **kwargs: (4650, 4927, "913"),
    )
    x, y, source = capture_mouse_xy()
    assert (x, y, source) == (4650, 4927, "xdotool*")


def test_capture_mouse_xy_prefers_vdisplay_probe(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.hmi.capture import capture_mouse_xy

    monkeypatch.setattr(
        "vdisplay.hmi.capture.probe_absolute_pointer",
        lambda **kwargs: ("gnome", (5200, 6100)),
    )
    x, y, source = capture_mouse_xy()
    assert (x, y, source) == (5200, 6100, "gnome")


def test_pick_context_coordinates_prefers_live_gnome() -> None:
    ctx = pick_context_coordinates(
        {"gnome": (5200, 6100), "xdotool": (1, 2)},
        stale_sources=("xdotool",),
        primary="evdev-rel",
    )
    assert ctx == (5200, 6100, "gnome")


def test_pick_context_coordinates_uses_stale_xdotool_hint() -> None:
    ctx = pick_context_coordinates(
        {"evdev-rel": (10, 20), "xdotool": (4670, 6487)},
        stale_sources=("xdotool",),
        primary="evdev-rel",
    )
    assert ctx == (4670, 6487, "xdotool*")


def test_sample_pointer_enriches_screen_and_app(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setattr("vdisplay.hmi.pointer.probe_gnome_shell_pointer", lambda: None)
    monkeypatch.setattr("vdisplay.hmi.pointer.probe_gtk_subprocess", lambda **kwargs: None)
    monkeypatch.setattr("vdisplay.hmi.pointer.probe_xdotool", lambda **kwargs: (5000, 100, "913"))
    monkeypatch.setattr(
        "vdisplay.hmi.pointer.monitor_at",
        lambda x, y, display=None: {"name": "DP-2", "x": 4096, "y": 0},
    )

    resolver = WindowContextResolver(display=":0")
    monkeypatch.setattr(
        resolver,
        "resolve",
        lambda x, y, window_id: {
            "window_id": "913",
            "title": "PyCharm Project",
            "app_label": "PyCharm",
            "process_name": "pycharm",
        },
    )

    history = {"xdotool": [(5000, 100)] * 8}
    sample = sample_pointer(
        source_history=history,
        use_gtk=False,
        evdev_xy=(63, 53),
        evdev_relative_only=True,
        window_resolver=resolver,
    )
    assert sample.primary == "evdev-rel"
    assert sample.monitor is not None
    assert sample.monitor["name"] == "DP-2"
    assert sample.app_label == "PyCharm"
    assert sample.window_title == "PyCharm Project"
    assert sample.context_source == "xdotool*"


def test_sample_pointer_prefers_gnome_on_wayland(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setattr("vdisplay.hmi.pointer.probe_gnome_shell_pointer", lambda: (5200, 6100))
    monkeypatch.setattr("vdisplay.hmi.pointer.probe_xdotool", lambda **kwargs: (1, 2, "9"))
    history: dict[str, list[tuple[int, int]]] = {}
    sample = sample_pointer(source_history=history, use_gtk=False)
    assert sample.primary == "gnome"
    assert sample.x == 5200


def test_sample_pointer_rejects_stale_xdotool_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setattr("vdisplay.hmi.pointer.probe_gnome_shell_pointer", lambda: None)
    monkeypatch.setattr("vdisplay.hmi.pointer.probe_gtk_subprocess", lambda **kwargs: None)
    monkeypatch.setattr("vdisplay.hmi.pointer.probe_xdotool", lambda **kwargs: (1, 2, "9"))
    history = {"xdotool": [(1, 2)] * 8}
    sample = sample_pointer(
        source_history=history,
        use_gtk=False,
        evdev_xy=(120, 45),
        evdev_relative_only=True,
    )
    assert sample.primary == "evdev-rel"
    assert sample.x == 120


def test_probe_absolute_skips_xdotool_on_wayland(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.hmi.pointer import probe_absolute_pointer

    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setattr("vdisplay.hmi.pointer.probe_gnome_shell_pointer", lambda: None)
    monkeypatch.setattr("vdisplay.hmi.pointer.probe_gtk_subprocess", lambda **kwargs: None)
    monkeypatch.setattr("vdisplay.hmi.pointer.probe_xdotool", lambda **kwargs: (_ for _ in ()).throw(AssertionError("xdotool should not run")))
    assert probe_absolute_pointer(use_gtk=True) is None


def test_run_hmi_watch_jsonl(monkeypatch: pytest.MonkeyPatch) -> None:
    sample = PointerSample(x=100, y=200, sources={"gnome": (100, 200)}, primary="gnome", monitor={"name": "DP-1"})

    monkeypatch.setattr("vdisplay.hmi.watch.sample_pointer", lambda **kwargs: sample)
    monkeypatch.setattr("vdisplay.hmi.watch.KeyboardWatcher", lambda: type("K", (), {"start": lambda s: None, "stop": lambda s: None, "drain": lambda s: [], "typed_buffer": ""})())
    monkeypatch.setattr(
        "vdisplay.hmi.watch.MouseWatcher",
        lambda: type(
            "M",
            (),
            {
                "start": lambda s: None,
                "stop": lambda s: None,
                "drain": lambda s: [],
                "position": None,
                "seed": lambda s, x, y: None,
                "move_count": 0,
                "relative_only": False,
            },
        )(),
    )
    monkeypatch.setattr("vdisplay.hmi.watch._seed_mouse", lambda *a, **k: [])

    buf = io.StringIO()
    rc = run_hmi_watch(interval=0.05, keyboard=False, mouse=False, jsonl=True, stream=buf, stop_after=0.06)
    assert rc == 0
    lines = [json.loads(line) for line in buf.getvalue().splitlines() if line.strip()]
    assert lines[0]["kind"] == "pointer"
    assert lines[0]["primary"] == "gnome"


def test_event_device_paths_parses_proc_input(tmp_path) -> None:
    devices = tmp_path / "devices"
    devices.write_text(
        'N: Name="Test keyboard"\n'
        "H: Handlers=kbd event3 \n\n"
        'N: Name="Touchpad"\n'
        "B: REL=143\n"
        "H: Handlers=mouse1 event4 \n",
        encoding="utf-8",
    )
    assert _event_device_paths(devices_path=devices) == [Path("/dev/input/event3")]
    assert _mouse_device_paths(devices_path=devices) == [Path("/dev/input/event4")]
