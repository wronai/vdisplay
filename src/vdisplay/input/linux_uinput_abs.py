"""Absolute-positioning virtual pointer via uinput (python-evdev).

Why this exists: ydotool's absolute coordinate space on a multi-monitor HiDPI
desktop proved opaque — the same command could land the cursor on the wrong
monitor, and no simple range (0-65535 over the desktop bbox) reproduced it.

An absolute pointing device we create OURSELVES has a coordinate space WE
define. The compositor maps our ABS range onto the desktop with a fixed linear
transform; a one-time per-monitor calibration (see
``coordinate_validation.calibrate_pointer_affine``) recovers it — measured as a
clean ~0.625 scale on the reference machine — after which positioning is
deterministic. Unlike ydotool, the input is stable and reproducible.

Requires write access to ``/dev/uinput`` (the user in the ``input`` group) and
the optional ``evdev`` dependency (``pip install "vdisplay[uinput]"``).
"""
from __future__ import annotations

import time
from typing import Any


class LinuxUinputAbsInput:
    """A virtual absolute mouse. Commands are in the device's ABS space; use a
    calibrated affine to convert capture pixels → ABS values per monitor."""

    def __init__(self, *, abs_max_x: int = 8416, abs_max_y: int = 7680, settle_s: float = 1.2) -> None:
        self._abs_max_x = abs_max_x
        self._abs_max_y = abs_max_y
        self._ui: Any = None
        self._e: Any = None
        self._settle_s = settle_s

    @staticmethod
    def available() -> tuple[bool, str]:
        import os

        try:
            from evdev import UInput  # noqa: F401
        except ImportError:
            return False, "python-evdev not installed (pip install 'vdisplay[uinput]')"
        if not os.access("/dev/uinput", os.W_OK):
            return False, "/dev/uinput not writable (add user to the 'input' group)"
        return True, "uinput absolute pointer available"

    def open(self) -> "LinuxUinputAbsInput":
        from evdev import AbsInfo, UInput
        from evdev import ecodes as e

        self._e = e
        caps = {
            e.EV_KEY: [e.BTN_LEFT, e.BTN_TOOL_MOUSE],
            e.EV_ABS: [
                (e.ABS_X, AbsInfo(0, 0, self._abs_max_x, 0, 0, 0)),
                (e.ABS_Y, AbsInfo(0, 0, self._abs_max_y, 0, 0, 0)),
            ],
        }
        self._ui = UInput(caps, name="vdisplay-abs-pointer", version=1)
        # give the compositor time to enumerate the new device before first use
        time.sleep(self._settle_s)
        return self

    def move_abs(self, x: int, y: int) -> None:
        if self._ui is None:
            self.open()
        e = self._e
        x = max(0, min(self._abs_max_x, int(x)))
        y = max(0, min(self._abs_max_y, int(y)))
        self._ui.write(e.EV_ABS, e.ABS_X, x)
        self._ui.write(e.EV_ABS, e.ABS_Y, y)
        self._ui.write(e.EV_KEY, e.BTN_TOOL_MOUSE, 1)
        self._ui.syn()

    def click(self, button: int = 1) -> None:
        if self._ui is None:
            self.open()
        e = self._e
        code = {1: e.BTN_LEFT}.get(button, e.BTN_LEFT)
        self._ui.write(e.EV_KEY, code, 1)
        self._ui.syn()
        self._ui.write(e.EV_KEY, code, 0)
        self._ui.syn()

    def move_abs_and_click(self, x: int, y: int, *, settle_s: float = 0.15) -> None:
        self.move_abs(x, y)
        time.sleep(settle_s)
        self.click(1)

    def close(self) -> None:
        if self._ui is not None:
            try:
                self._ui.close()
            finally:
                self._ui = None

    def __enter__(self) -> "LinuxUinputAbsInput":
        return self.open()

    def __exit__(self, *exc: object) -> None:
        self.close()
