"""Live HMI watch loop — pointer + keyboard in the shell."""

from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict
from datetime import datetime
from typing import Any, TextIO

from .context import WindowContextResolver
from .keyboard import KeyEvent, KeyboardWatcher
from .mouse import MouseMove, MouseWatcher
from .pointer import (
    PointerSample,
    is_wayland_session,
    pointer_probe_errors,
    probe_absolute_pointer,
    sample_pointer,
)


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _format_screen(monitor: dict[str, Any] | None) -> str:
    if not monitor:
        return "?"
    name = str(monitor.get("name") or monitor.get("label") or "?")
    left = monitor.get("x")
    top = monitor.get("y")
    if left is not None and top is not None:
        return f"{name}@{left},{top}"
    return name


def _truncate(text: str, limit: int = 48) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _print_pointer_line(sample: PointerSample, *, typed: str, stream: TextIO) -> None:
    screen = _format_screen(sample.monitor)
    app = sample.app_label or sample.process_name or "?"
    window = sample.window_title or sample.window_id or "?"
    if isinstance(window, str):
        window = _truncate(window)
    typed_show = typed if typed else ""
    err = f"  ! {sample.error}" if sample.error else ""
    ctx = ""
    if sample.context_source and sample.context_x is not None and sample.context_y is not None:
        ctx = f"  ctx={sample.context_source}@({sample.context_x},{sample.context_y})"
    print(
        f"[{_ts()}] ptr {sample.primary_label()}  screen={screen}  app={app}  window={window!r}{ctx}  typed={typed_show!r}{err}",
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


def _seed_mouse(
    mouse_watcher: MouseWatcher,
    *,
    display: str | None,
    seed_xy: tuple[int, int] | None,
) -> list[str]:
    warnings: list[str] = []
    if seed_xy is not None:
        mouse_watcher.seed(*seed_xy)
        return warnings

    absolute = probe_absolute_pointer(display=display, use_gtk=True)
    if absolute is not None:
        source, xy = absolute
        mouse_watcher.seed(*xy)
        warnings.append(f"seeded evdev from {source}=({xy[0]},{xy[1]})")
        return warnings

    if is_wayland_session():
        warnings.append(
            "absolute pointer seed failed (gnome/gtk unavailable) — move mouse to start evdev-rel tracking"
        )
        errors = pointer_probe_errors()
        detail = "; ".join(f"{k}={v}" for k, v in errors.items() if v)
        if detail:
            warnings.append(detail)
    return warnings


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
        for warning in _seed_mouse(mouse_watcher, display=display, seed_xy=seed_xy):
            if not jsonl:
                prefix = "info" if warning.startswith("seeded ") else "warning"
                print(f"{prefix}: {warning}", flush=True, file=err)

    source_history: dict[str, list[tuple[int, int]]] = {}
    window_resolver = WindowContextResolver(display=display)
    pointer_mode = "evdev+gnome+gtk" if wayland else "xdotool+gtk"
    if wayland:
        pointer_mode += " (Wayland: ignore stale xdotool)"

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

            if mouse and time.monotonic() - last_resync >= 2.0:
                if mouse_watcher.relative_only or mouse_watcher.position is None:
                    absolute = probe_absolute_pointer(display=display, use_gtk=use_gtk)
                    if absolute is not None:
                        mouse_watcher.seed(*absolute[1])
                last_resync = time.monotonic()

            sample = sample_pointer(
                display=display,
                use_gtk=use_gtk,
                gtk_every=gtk_every,
                tick=tick,
                evdev_xy=mouse_watcher.position if mouse else None,
                evdev_relative_only=mouse_watcher.relative_only if mouse else False,
                source_history=source_history,
                window_resolver=window_resolver,
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
                    "context_x": sample.context_x,
                    "context_y": sample.context_y,
                    "context_source": sample.context_source,
                    "screen": sample.monitor.get("name") if sample.monitor else None,
                    "monitor": sample.monitor,
                    "window_id": sample.window_id,
                    "window_title": sample.window_title,
                    "app": sample.app_label,
                    "process_name": sample.process_name,
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
