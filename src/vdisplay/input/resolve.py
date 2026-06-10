"""Pick pointer/keyboard backend for the current host session."""

from __future__ import annotations

import os
from typing import Protocol

from ..capture.linux_xwd import _is_wayland_session
from .linux_xdotool import LinuxXdotoolInput
from .linux_ydotool import LinuxYdotoolInput


class PointerInput(Protocol):
    def move(self, x: int, y: int) -> None: ...
    def click(self, button: int = 1) -> None: ...
    def type_text(self, text: str) -> None: ...


def resolve_pointer_input(*, display: str | None = None) -> tuple[PointerInput, str]:
    """Return (input driver, method label). Prefer ydotool on Wayland hosts."""
    if _is_wayland_session():
        ready, _reason = LinuxYdotoolInput.available()
        if ready:
            return LinuxYdotoolInput(), "ydotool"
    from ..discovery import resolve_host_display

    return LinuxXdotoolInput(resolve_host_display(display or os.environ.get("DISPLAY"))), "xdotool"
