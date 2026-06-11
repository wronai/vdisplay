"""Terminal formatting helpers for HMI watch output."""

from __future__ import annotations

import sys
from datetime import datetime
from typing import Any, TextIO

from .keyboard import KeyEvent
from .mouse import MouseMove
from .pointer import PointerSample


def ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def format_screen(monitor: dict[str, Any] | None) -> str:
    if not monitor:
        return "?"
    name = str(monitor.get("name") or monitor.get("label") or "?")
    left = monitor.get("x")
    top = monitor.get("y")
    if left is not None and top is not None:
        return f"{name}@{left},{top}"
    return name


def truncate(text: str, limit: int = 48) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def print_pointer_line(sample: PointerSample, *, typed: str, stream: TextIO) -> None:
    screen = format_screen(sample.monitor)
    app = sample.app_label or sample.process_name or "?"
    window = sample.window_title or sample.window_id or "?"
    if isinstance(window, str):
        window = truncate(window)
    typed_show = typed if typed else ""
    err = f"  ! {sample.error}" if sample.error else ""
    ctx = ""
    if sample.context_source and sample.context_x is not None and sample.context_y is not None:
        ctx = f"  ctx={sample.context_source}@({sample.context_x},{sample.context_y})"
    print(
        f"[{ts()}] ptr {sample.primary_label()}  screen={screen}  app={app}  window={window!r}{ctx}  typed={typed_show!r}{err}",
        flush=True,
        file=stream,
    )


def print_key_event(event: KeyEvent, *, typed: str, stream: TextIO) -> None:
    char = f" char={event.char!r}" if event.char else ""
    print(
        f"[{ts()}] key {event.name}{char}  typed={typed!r}",
        flush=True,
        file=stream,
    )


def print_mouse_move(move: MouseMove, stream: TextIO) -> None:
    delta = ""
    if move.dx or move.dy:
        delta = f" d=({move.dx:+d},{move.dy:+d})"
    print(
        f"[{ts()}] move {move.source}=({move.x},{move.y}){delta}",
        flush=True,
        file=stream,
    )


def print_warning(message: str, *, stream: TextIO | None = None) -> None:
    print(f"warning: {message}", flush=True, file=stream or sys.stderr)
