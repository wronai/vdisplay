"""Live HMI watch loop — pointer + keyboard in the shell."""

from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict
from datetime import datetime
from typing import Any, TextIO

from .keyboard import KeyEvent, KeyboardWatcher
from .mouse import MouseMove, MouseWatcher
from .pointer import PointerSample, is_wayland_session, probe_gtk_subprocess, sample_pointer


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _format_monitor(monitor: dict[str, Any] | None) -> str:
    if not monitor:
        return "-"
    name = str(monitor.get("name") or monitor.get("label") or "?")
    left = monitor.get("x")
    top = monitor.get("y")
    if left is not None and top is not None:
        return f"{name}@{left},{top}"
    return name


def _print_pointer_line(sample: PointerSample, *, typed: str, stream: TextIO) -> None:
    mon = _format_monitor(sample.monitor)
    win = sample.window_title or sample.window_id or "-"
    if len(win) > 48:
        win = win[:45] + "..."
    typed_show = typed if typed else ""
    err = f"  ! {sample.error}" if sample.error else ""
    print(
        f"[{_ts()}] ptr {sample.primary_label()}  mon={mon}  win={win}  typed={typed_show!r}{err}",
        flush=True,
        file=stream,
    )


def _print_key_event(event: KeyEvent, *, typed: str, stream: TextIO) -> None:
    char = f" char={event.char!r}" if event.char else ""
    print(
        f"[{_ts()}] key {event.name}{char}  typed={typed!r}",
        flush=True,
        file=stream,
    )


def _print_mouse_move(move: MouseMove, stream: TextIO) -> None:
    delta = ""
    if move.dx or move.dy:
        delta = f" d=({move.dx:+d},{move.dy:+d})"
    print(
        f"[{_ts()}] move {move.source}=({move.x},{move.y}){delta}",
        flush=True,
        file=stream,
    )


def _seed_mouse(mouse_watcher: MouseWatcher, *, display: str | None, err: TextIO) -> str | None:
    gtk = probe_gtk_subprocess()
    if gtk is not None:
        mouse_watcher.seed(*gtk)
        return None
    if is_wayland_session():
        return "GTK pointer seed failed — move mouse after start; evdev relative tracking needs initial seed"
    xdotool_only = "waiting for first mouse motion via evdev"
    return xdotool_only


def run_hmi_watch(
    *,
    interval: float = 0.25,
    display: str | None = None,
    use_gtk: bool = True,
    gtk_every: int | None = None,
    keyboard: bool = True,
    mouse: bool = True,
    jsonl: bool = False,
    stream: TextIO | None = None,
    stop_after: float | None = None,
) -> int:
    """Stream pointer position and keyboard events until interrupted."""
    out = stream or sys.stdout
    err = sys.stderr
    interval = max(0.05, float(interval))
    tick = 0
    started = time.monotonic()
    wayland = is_wayland_session()
    if gtk_every is None:
        gtk_every = 1 if wayland else 4

    keyboard_watcher = KeyboardWatcher()
    keyboard_error: str | None = None
    if keyboard:
        keyboard_error = keyboard_watcher.start()

    mouse_watcher = MouseWatcher()
    mouse_error: str | None = None
    if mouse:
        mouse_error = mouse_watcher.start()
        seed_error = _seed_mouse(mouse_watcher, display=display, err=err)
        if seed_error and not jsonl:
            print(f"warning: {seed_error}", flush=True, file=err)

    source_history: dict[str, list[tuple[int, int]]] = {}
    pointer_mode = "evdev+gtk" if wayland and mouse else ("xdotool+gtk" if use_gtk else "xdotool")
    if wayland:
        pointer_mode = f"{pointer_mode} (Wayland: evdev/gtk, not xdotool)"

    if not jsonl:
        print(
            f"vdisplay hmi watch — Ctrl+C to stop | interval={interval:.2f}s | "
            f"pointer={pointer_mode} | keyboard={'evdev' if keyboard else 'off'}",
            flush=True,
            file=err,
        )
        if keyboard_error:
            print(f"warning: {keyboard_error}", flush=True, file=err)
        if mouse_error:
            print(f"warning: {mouse_error}", flush=True, file=err)

    last_resync = time.monotonic()
    try:
        while True:
            if stop_after is not None and time.monotonic() - started >= stop_after:
                break

            for item in keyboard_watcher.drain():
                if isinstance(item, str):
                    if not jsonl:
                        print(f"warning: {item}", flush=True, file=err)
                    continue
                if jsonl:
                    print(
                        json.dumps(
                            {
                                "ts": _ts(),
                                "kind": "key",
                                "event": asdict(item),
                                "typed": keyboard_watcher.typed_buffer,
                            },
                            ensure_ascii=False,
                        ),
                        flush=True,
                        file=out,
                    )
                else:
                    _print_key_event(item, typed=keyboard_watcher.typed_buffer, stream=out)

            for item in mouse_watcher.drain():
                if isinstance(item, str):
                    if not jsonl:
                        print(f"warning: {item}", flush=True, file=err)
                    continue
                if not jsonl:
                    _print_mouse_move(item, stream=out)

            if mouse and use_gtk and wayland and time.monotonic() - last_resync >= 2.0:
                gtk = probe_gtk_subprocess()
                if gtk is not None and mouse_watcher.move_count == 0:
                    mouse_watcher.seed(*gtk)
                last_resync = time.monotonic()

            sample = sample_pointer(
                display=display,
                use_gtk=use_gtk,
                gtk_every=gtk_every,
                tick=tick,
                evdev_xy=mouse_watcher.position if mouse else None,
                source_history=source_history,
            )
            if jsonl:
                payload = {
                    "ts": _ts(),
                    "kind": "pointer",
                    "x": sample.x,
                    "y": sample.y,
                    "primary": sample.primary,
                    "sources": {k: list(v) for k, v in sample.sources.items()},
                    "stale_sources": list(sample.stale_sources),
                    "monitor": sample.monitor.get("name") if sample.monitor else None,
                    "window_id": sample.window_id,
                    "window_title": sample.window_title,
                    "typed": keyboard_watcher.typed_buffer,
                    "error": sample.error,
                }
                print(json.dumps(payload, ensure_ascii=False), flush=True, file=out)
            else:
                _print_pointer_line(sample, typed=keyboard_watcher.typed_buffer, stream=out)

            tick += 1
            time.sleep(interval)
    except KeyboardInterrupt:
        if not jsonl:
            print(f"\n[{_ts()}] stopped", flush=True, file=err)
    finally:
        keyboard_watcher.stop()
        mouse_watcher.stop()

    return 0
