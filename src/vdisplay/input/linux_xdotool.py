from __future__ import annotations

import shutil

from ..utils import require_command, run_command


class LinuxXdotoolInput:
    def __init__(self, display: str | None = None) -> None:
        self.display = display

    def _env(self) -> dict[str, str]:
        if self.display is None:
            return {}
        return {"DISPLAY": self.display}

    @staticmethod
    def available() -> tuple[bool, str]:
        if shutil.which("xdotool") is None:
            return False, "xdotool not installed"
        return True, "xdotool available"

    def can_type(self) -> bool:
        if shutil.which("xdotool") is None:
            return False
        # xdotool typing works for X11/XWayland clients only.
        # On a native Wayland session it can move/click but not type into
        # Wayland-native windows.
        from ..capture.linux_xwd import _is_wayland_session

        if _is_wayland_session():
            return False
        return True

    def can_paste(self) -> bool:
        return self.can_type()

    def move(self, x: int, y: int) -> None:
        require_command("xdotool")
        run_command(
            ["xdotool", "mousemove", str(x), str(y)],
            env=self._env(),
            text=True,
        )

    def click(self, button: int = 1) -> None:
        require_command("xdotool")
        run_command(
            ["xdotool", "click", str(button)],
            env=self._env(),
            text=True,
        )

    def type_text(self, text: str) -> None:
        require_command("xdotool")
        run_command(
            ["xdotool", "type", "--", text],
            env=self._env(),
            text=True,
        )

    def hotkey(self, *keys: str) -> None:
        require_command("xdotool")
        run_command(
            ["xdotool", "key", *keys],
            env=self._env(),
            text=True,
        )
