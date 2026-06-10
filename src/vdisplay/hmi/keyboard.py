"""Keyboard event watch via Linux evdev (stdlib only)."""

from __future__ import annotations

import errno
import os
import queue
import select
import struct
import threading
from dataclasses import dataclass
from pathlib import Path

EV_KEY = 0x01
EV_SYN = 0x00
KEY_PRESS = 1
KEY_RELEASE = 0

# Linux keycodes for printable US QWERTY (subset of input-event-codes.h)
_KEYCODE_CHARS: dict[int, str] = {
    2: "1",
    3: "2",
    4: "3",
    5: "4",
    6: "5",
    7: "6",
    8: "7",
    9: "8",
    10: "9",
    11: "0",
    16: "q",
    17: "w",
    18: "e",
    19: "r",
    20: "t",
    21: "y",
    22: "u",
    23: "i",
    24: "o",
    25: "p",
    30: "a",
    31: "s",
    32: "d",
    33: "f",
    34: "g",
    35: "h",
    36: "j",
    37: "k",
    38: "l",
    44: "z",
    45: "x",
    46: "c",
    47: "v",
    48: "b",
    49: "n",
    50: "m",
    51: ",",
    52: ".",
    53: "/",
    57: " ",
    12: "-",
    13: "=",
    26: "[",
    27: "]",
    39: ";",
    40: "'",
    43: "\\",
    41: "`",
}

_KEYCODE_SHIFT_CHARS: dict[int, str] = {
    2: "!",
    3: "@",
    4: "#",
    5: "$",
    6: "%",
    7: "^",
    8: "&",
    9: "*",
    10: "(",
    11: ")",
    16: "Q",
    17: "W",
    18: "E",
    19: "R",
    20: "T",
    21: "Y",
    22: "U",
    23: "I",
    24: "O",
    25: "P",
    30: "A",
    31: "S",
    32: "D",
    33: "F",
    34: "G",
    35: "H",
    36: "J",
    37: "K",
    38: "L",
    44: "Z",
    45: "X",
    46: "C",
    47: "V",
    48: "B",
    49: "N",
    50: "M",
    51: "<",
    52: ">",
    53: "?",
    12: "_",
    13: "+",
    26: "{",
    27: "}",
    39: ":",
    40: '"',
    43: "|",
    41: "~",
}

_KEYCODE_NAMES: dict[int, str] = {
    1: "ESC",
    14: "BACKSPACE",
    15: "TAB",
    28: "ENTER",
    29: "LEFTCTRL",
    42: "LEFTSHIFT",
    54: "RIGHTSHIFT",
    56: "LEFTALT",
    58: "CAPSLOCK",
    97: "RIGHTCTRL",
    100: "RIGHTALT",
    103: "UP",
    105: "LEFT",
    106: "RIGHT",
    108: "DOWN",
    110: "INSERT",
    111: "DELETE",
    125: "SUPER",
}

_SHIFT_KEYS = {42, 54}
_CTRL_KEYS = {29, 97}
_ALT_KEYS = {56, 100}


@dataclass(frozen=True)
class KeyEvent:
    code: int
    name: str
    action: str
    char: str | None
    typed_fragment: str | None


def _event_device_paths(*, devices_path: Path | None = None) -> list[Path]:
    devices = devices_path or Path("/proc/bus/input/devices")
    if not devices.is_file():
        return []
    paths: list[Path] = []
    for block in devices.read_text(encoding="utf-8", errors="replace").split("\n\n"):
        if "Handlers=" not in block:
            continue
        name = ""
        handlers = ""
        for line in block.splitlines():
            if line.startswith("N: Name="):
                name = line
            elif line.startswith("H: Handlers="):
                handlers = line.split("=", 1)[-1]
        if "kbd" not in handlers.split() and "keyboard" not in name.lower():
            continue
        for token in handlers.split():
            if token.startswith("event"):
                paths.append(Path("/dev/input") / token)
    return paths


def _decode_char(code: int, *, shift: bool) -> str | None:
    if shift:
        return _KEYCODE_SHIFT_CHARS.get(code) or _KEYCODE_CHARS.get(code)
    return _KEYCODE_CHARS.get(code)


def _key_name(code: int) -> str:
    return _KEYCODE_NAMES.get(code, f"KEY_{code}")


class KeyboardWatcher:
    """Background evdev reader pushing :class:`KeyEvent` objects to a queue."""

    def __init__(self) -> None:
        self._queue: queue.Queue[KeyEvent | str] = queue.Queue()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._typed = ""
        self._shift = False

    @property
    def typed_buffer(self) -> str:
        return self._typed

    def start(self) -> str | None:
        paths = _event_device_paths()
        if not paths:
            return "no keyboard devices found under /dev/input"
        self._thread = threading.Thread(target=self._run, args=(paths,), name="vdisplay-hmi-keyboard", daemon=True)
        self._thread.start()
        return None

    def stop(self) -> None:
        self._stop.set()

    def drain(self) -> list[KeyEvent | str]:
        out: list[KeyEvent | str] = []
        while True:
            try:
                out.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return out

    def _emit(self, item: KeyEvent | str) -> None:
        self._queue.put(item)

    def _handle_key(self, code: int, value: int) -> None:
        if code in _SHIFT_KEYS:
            self._shift = value == KEY_PRESS
            return
        if value != KEY_PRESS:
            return

        name = _key_name(code)
        char = _decode_char(code, shift=self._shift)
        fragment: str | None = None

        if code == 28:  # Enter
            fragment = self._typed
            self._typed = ""
        elif code == 14:  # Backspace
            self._typed = self._typed[:-1]
        elif char is not None and code not in (_CTRL_KEYS | _ALT_KEYS):
            self._typed += char
            fragment = char

        self._emit(
            KeyEvent(
                code=code,
                name=name,
                action="press",
                char=char,
                typed_fragment=fragment,
            )
        )

    def _run(self, paths: list[Path]) -> None:
        fds: dict[int, Path] = {}
        for path in paths:
            try:
                fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
            except OSError as exc:
                if exc.errno in {errno.EACCES, errno.EPERM}:
                    self._emit(
                        "keyboard: permission denied for /dev/input — add user to group 'input' or run with sufficient privileges"
                    )
                    return
                continue
            fds[fd] = path

        if not fds:
            self._emit("keyboard: could not open any /dev/input/event* nodes")
            return

        event_struct = struct.Struct("llHHi")
        while not self._stop.is_set():
            readable, _, _ = select.select(list(fds.keys()), [], [], 0.2)
            for fd in readable:
                try:
                    while True:
                        chunk = os.read(fd, event_struct.size * 32)
                        if not chunk:
                            break
                        for offset in range(0, len(chunk) - event_struct.size + 1, event_struct.size):
                            _sec, _usec, ev_type, code, value = event_struct.unpack_from(chunk, offset)
                            if ev_type != EV_KEY:
                                continue
                            self._handle_key(code, value)
                except BlockingIOError:
                    continue
                except OSError:
                    break

        for fd in fds:
            try:
                os.close(fd)
            except OSError:
                pass
