"""Mouse position watch via Linux evdev REL/ABS events."""

from __future__ import annotations

import errno
import os
import queue
import select
import struct
import threading
from dataclasses import dataclass
from pathlib import Path

EV_REL = 0x02
EV_ABS = 0x03
REL_X = 0x00
REL_Y = 0x01
ABS_X = 0x00
ABS_Y = 0x01


@dataclass(frozen=True)
class MouseMove:
    x: int
    y: int
    dx: int = 0
    dy: int = 0
    source: str = "evdev"


def _parse_device_blocks(devices_path: Path) -> list[dict[str, object]]:
    if not devices_path.is_file():
        return []
    blocks: list[dict[str, object]] = []
    for block in devices_path.read_text(encoding="utf-8", errors="replace").split("\n\n"):
        if "Handlers=" not in block:
            continue
        name = ""
        handlers = ""
        has_rel = False
        for line in block.splitlines():
            if line.startswith("N: Name="):
                name = line.split('"', 1)[-1].rstrip('"')
            elif line.startswith("H: Handlers="):
                handlers = line.split("=", 1)[-1]
            elif line.startswith("B: REL=") or " REL" in line:
                has_rel = True
        blocks.append({"name": name, "handlers": handlers, "has_rel": has_rel})
    return blocks


def _is_mouse_handler(tokens: list[str]) -> bool:
    return any(token.startswith("mouse") for token in tokens)


def _is_pointer_name(name: str) -> bool:
    lowered = name.lower()
    return any(token in lowered for token in ("mouse", "pointer", "trackball", "touchpad", "trackpoint"))


def _mouse_device_paths(*, devices_path: Path | None = None) -> list[Path]:
    devices = devices_path or Path("/proc/bus/input/devices")
    primary: list[Path] = []
    fallback: list[Path] = []
    seen: set[str] = set()
    for block in _parse_device_blocks(devices):
        name = str(block.get("name") or "")
        handlers = str(block.get("handlers") or "")
        has_rel = bool(block.get("has_rel"))
        tokens = handlers.split()
        has_mouse_handler = _is_mouse_handler(tokens)
        is_pointer_name = _is_pointer_name(name)
        if not has_mouse_handler and not (has_rel and is_pointer_name):
            continue
        for token in tokens:
            if not token.startswith("event"):
                continue
            path = str(Path("/dev/input") / token)
            if path in seen:
                continue
            seen.add(path)
            (primary if has_mouse_handler else fallback).append(Path(path))
    return primary or fallback


class MouseWatcher:
    """Track pointer position from evdev relative/absolute motion events."""

    def __init__(self) -> None:
        self._queue: queue.Queue[MouseMove | str] = queue.Queue()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._x: int | None = None
        self._y: int | None = None
        self._moves = 0
        self._seeded = False

    @property
    def position(self) -> tuple[int, int] | None:
        with self._lock:
            if self._x is None or self._y is None:
                return None
            return self._x, self._y

    @property
    def relative_only(self) -> bool:
        with self._lock:
            return self._x is not None and not self._seeded

    @property
    def move_count(self) -> int:
        return self._moves

    def seed(self, x: int, y: int) -> None:
        with self._lock:
            self._x = int(x)
            self._y = int(y)
            self._seeded = True

    def start(self) -> str | None:
        paths = _mouse_device_paths()
        if not paths:
            return "no pointer devices found under /dev/input (looked for REL/mouse/touchpad)"
        self._thread = threading.Thread(target=self._run, args=(paths,), name="vdisplay-hmi-mouse", daemon=True)
        self._thread.start()
        return None

    def stop(self) -> None:
        self._stop.set()

    def drain(self) -> list[MouseMove | str]:
        out: list[MouseMove | str] = []
        while True:
            try:
                out.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return out

    def _ensure_origin(self) -> None:
        if self._x is None:
            self._x = 0
            self._y = 0

    def _apply_rel(self, dx: int, dy: int) -> None:
        with self._lock:
            self._ensure_origin()
            assert self._x is not None and self._y is not None
            self._x += int(dx)
            self._y += int(dy)
            self._moves += 1
            pos = (self._x, self._y)
            source = "evdev-rel" if not self._seeded else "evdev"
        self._queue.put(MouseMove(x=pos[0], y=pos[1], dx=dx, dy=dy, source=source))

    def _apply_abs(self, axis: int, value: int) -> None:
        with self._lock:
            self._ensure_origin()
            if axis == ABS_X:
                self._x = int(value)
            elif axis == ABS_Y:
                self._y = int(value)
            else:
                return
            self._seeded = True
            self._moves += 1
            assert self._x is not None and self._y is not None
            pos = (self._x, self._y)
        self._queue.put(MouseMove(x=pos[0], y=pos[1], source="evdev"))

    def _open_device_fds(self, paths: list[Path]) -> dict[int, Path] | None:
        fds: dict[int, Path] = {}
        for path in paths:
            try:
                fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
            except OSError as exc:
                if exc.errno in {errno.EACCES, errno.EPERM}:
                    self._queue.put(
                        "mouse: permission denied for /dev/input — re-login after: sudo usermod -aG input $USER"
                    )
                    return None
                continue
            fds[fd] = path

        if not fds:
            self._queue.put("mouse: could not open any /dev/input/event* nodes")
            return None
        return fds

    def _process_event(self, ev_type: int, code: int, value: int) -> None:
        if ev_type == EV_REL:
            if code == REL_X:
                self._apply_rel(value, 0)
            elif code == REL_Y:
                self._apply_rel(0, value)
        elif ev_type == EV_ABS:
            self._apply_abs(code, value)

    def _read_events_from_fd(self, fd: int, event_struct: struct.Struct) -> bool:
        try:
            while True:
                chunk = os.read(fd, event_struct.size * 64)
                if not chunk:
                    return True
                for offset in range(0, len(chunk) - event_struct.size + 1, event_struct.size):
                    _sec, _usec, ev_type, code, value = event_struct.unpack_from(chunk, offset)
                    self._process_event(ev_type, code, value)
        except BlockingIOError:
            return True
        except OSError:
            return False
        return True

    def _run(self, paths: list[Path]) -> None:
        fds = self._open_device_fds(paths)
        if fds is None:
            return

        event_struct = struct.Struct("llHHi")
        while not self._stop.is_set():
            readable, _, _ = select.select(list(fds.keys()), [], [], 0.2)
            for fd in readable:
                if not self._read_events_from_fd(fd, event_struct):
                    break

        for fd in fds:
            try:
                os.close(fd)
            except OSError:
                pass
