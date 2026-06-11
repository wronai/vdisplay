"""Live HMI watch loop — pointer + keyboard in the shell."""

from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict
from typing import Any, TextIO

from .context import WindowContextResolver
from .keyboard import KeyboardWatcher
from .mouse import MouseWatcher
from .pointer import (
    is_wayland_session,
    probe_absolute_pointer,
    sample_pointer,
)
from .watch_format import print_key_event, print_mouse_move, print_pointer_line, print_warning, ts
from .watch_seed import seed_mouse_watcher

_seed_mouse = seed_mouse_watcher


def _emit_jsonl_pointer(
    sample: Any,
    *,
    typed: str,
    stream: TextIO,
) -> None:
    payload = {
        "ts": ts(),
        "kind": "pointer",
        "x": sample.x,
        "y": sample.y,
        "primary": sample.primary,
        "sources": {k: list(v) for k, v in sample.sources.items()},
        "stale_sources": list(sample.stale_sources),
        "context_x": sample.context_x,
        "context_y": sample.context_y,
        "context_source": sample.context_source,
        "screen": sample.monitor.get("name") if sample.monitor else None,
        "monitor": sample.monitor,
        "window_id": sample.window_id,
        "window_title": sample.window_title,
        "app": sample.app_label,
        "process_name": sample.process_name,
        "typed": typed,
        "error": sample.error,
    }
    print(json.dumps(payload, ensure_ascii=False), flush=True, file=stream)


def _seed_and_warn(
    mouse_watcher: MouseWatcher,
    *,
    display: str | None,
    seed_xy: tuple[int, int] | None,
    jsonl: bool,
    err: TextIO,
) -> None:
    for warning in _seed_mouse(mouse_watcher, display=display, seed_xy=seed_xy):
        if not jsonl:
            prefix = "info" if warning.startswith("seeded ") else "warning"
            print(f"{prefix}: {warning}", flush=True, file=err)


def _print_startup(
    *,
    jsonl: bool,
    err: TextIO,
    interval: float,
    pointer_mode: str,
    keyboard: bool,
    keyboard_error: str | None,
    mouse_error: str | None,
) -> None:
    if jsonl:
        return
    print(
        f"vdisplay hmi watch — Ctrl+C to stop | interval={interval:.2f}s | "
        f"pointer={pointer_mode} | keyboard={'evdev' if keyboard else 'off'}",
        flush=True,
        file=err,
    )
    if keyboard_error:
        print_warning(keyboard_error, stream=err)
    if mouse_error:
        print_warning(mouse_error, stream=err)


def _drain_keyboard(
    watcher: KeyboardWatcher,
    *,
    jsonl: bool,
    out: TextIO,
    err: TextIO,
) -> None:
    for item in watcher.drain():
        if isinstance(item, str):
            if not jsonl:
                print_warning(item, stream=err)
            continue
        if jsonl:
            payload = {
                "ts": ts(),
                "kind": "key",
                "event": asdict(item),
                "typed": watcher.typed_buffer,
            }
            print(json.dumps(payload, ensure_ascii=False), flush=True, file=out)
        else:
            print_key_event(item, typed=watcher.typed_buffer, stream=out)


def _drain_mouse(
    watcher: MouseWatcher,
    *,
    jsonl: bool,
    out: TextIO,
    err: TextIO,
) -> None:
    for item in watcher.drain():
        if isinstance(item, str):
            if not jsonl:
                print_warning(item, stream=err)
            continue
        if not jsonl:
            print_mouse_move(item, stream=out)


def _maybe_resync_mouse(
    mouse_watcher: MouseWatcher,
    *,
    display: str | None,
    use_gtk: bool,
    last_resync: float,
) -> float:
    if time.monotonic() - last_resync < 2.0:
        return last_resync
    if mouse_watcher.relative_only or mouse_watcher.position is None:
        absolute = probe_absolute_pointer(display=display, use_gtk=use_gtk)
        if absolute is not None:
            mouse_watcher.seed(*absolute[1])
    return time.monotonic()


def _emit_pointer(
    sample: Any,
    *,
    jsonl: bool,
    typed: str,
    stream: TextIO,
) -> None:
    if jsonl:
        _emit_jsonl_pointer(sample, typed=typed, stream=stream)
    else:
        print_pointer_line(sample, typed=typed, stream=stream)


def _setup_watchers(
    *,
    keyboard: bool,
    mouse: bool,
    display: str | None,
    seed_xy: tuple[int, int] | None,
    jsonl: bool,
    err: TextIO,
) -> tuple[KeyboardWatcher, MouseWatcher, str | None, str | None]:
    keyboard_watcher = KeyboardWatcher()
    keyboard_error: str | None = keyboard_watcher.start() if keyboard else None

    mouse_watcher = MouseWatcher()
    mouse_error: str | None = None
    if mouse:
        mouse_error = mouse_watcher.start()
        _seed_and_warn(mouse_watcher, display=display, seed_xy=seed_xy, jsonl=jsonl, err=err)

    return keyboard_watcher, mouse_watcher, keyboard_error, mouse_error


def _run_watch_loop(
    *,
    interval: float,
    stop_after: float | None,
    started: float,
    display: str | None,
    use_gtk: bool,
    gtk_every: int,
    mouse_watcher: MouseWatcher,
    keyboard_watcher: KeyboardWatcher,
    source_history: dict[str, list[tuple[int, int]]],
    window_resolver: WindowContextResolver,
    jsonl: bool,
    out: TextIO,
) -> None:
    last_resync = time.monotonic()
    tick = 0
    try:
        while True:
            if stop_after is not None and time.monotonic() - started >= stop_after:
                break

            _drain_keyboard(keyboard_watcher, jsonl=jsonl, out=out, err=sys.stderr)
            _drain_mouse(mouse_watcher, jsonl=jsonl, out=out, err=sys.stderr)
            last_resync = _maybe_resync_mouse(
                mouse_watcher, display=display, use_gtk=use_gtk, last_resync=last_resync
            )
            sample = sample_pointer(
                display=display,
                use_gtk=use_gtk,
                gtk_every=gtk_every,
                tick=tick,
                evdev_xy=mouse_watcher.position if mouse_watcher else None,
                evdev_relative_only=mouse_watcher.relative_only if mouse_watcher else False,
                source_history=source_history,
                window_resolver=window_resolver,
            )
            _emit_pointer(sample, jsonl=jsonl, typed=keyboard_watcher.typed_buffer, stream=out)

            tick += 1
            time.sleep(interval)
    except KeyboardInterrupt:
        if not jsonl:
            print(f"\n[{ts()}] stopped", flush=True, file=sys.stderr)
    finally:
        keyboard_watcher.stop()
        mouse_watcher.stop()


def run_hmi_watch(
    *,
    interval: float = 0.25,
    display: str | None = None,
    use_gtk: bool = True,
    gtk_every: int | None = None,
    keyboard: bool = True,
    mouse: bool = True,
    seed_xy: tuple[int, int] | None = None,
    jsonl: bool = False,
    stream: TextIO | None = None,
    stop_after: float | None = None,
) -> int:
    """Stream pointer position and keyboard events until interrupted."""
    out = stream or sys.stdout
    err = sys.stderr
    interval = max(0.05, float(interval))
    started = time.monotonic()
    wayland = is_wayland_session()
    if gtk_every is None:
        gtk_every = 1 if wayland else 4

    keyboard_watcher, mouse_watcher, keyboard_error, mouse_error = _setup_watchers(
        keyboard=keyboard,
        mouse=mouse,
        display=display,
        seed_xy=seed_xy,
        jsonl=jsonl,
        err=err,
    )

    source_history: dict[str, list[tuple[int, int]]] = {}
    window_resolver = WindowContextResolver(display=display)
    pointer_mode = "evdev+gnome+gtk" if wayland else "xdotool+gtk"
    if wayland:
        pointer_mode += " (Wayland: ignore stale xdotool)"

    _print_startup(
        jsonl=jsonl,
        err=err,
        interval=interval,
        pointer_mode=pointer_mode,
        keyboard=keyboard,
        keyboard_error=keyboard_error,
        mouse_error=mouse_error,
    )

    _run_watch_loop(
        interval=interval,
        stop_after=stop_after,
        started=started,
        display=display,
        use_gtk=use_gtk,
        gtk_every=gtk_every,
        mouse_watcher=mouse_watcher,
        keyboard_watcher=keyboard_watcher,
        source_history=source_history,
        window_resolver=window_resolver,
        jsonl=jsonl,
        out=out,
    )

    return 0
