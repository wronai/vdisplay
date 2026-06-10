"""Wayland pointer/keyboard injection via ydotool (uinput)."""

from __future__ import annotations

import os
import shutil

from ..utils import require_command, run_command


def _ydotool_env() -> dict[str, str]:
    env: dict[str, str] = {}
    for sock in (os.environ.get("YDOTOOL_SOCKET"), "/tmp/.ydotool_socket", os.path.expanduser("~/.ydotool_socket")):
        if sock and os.path.exists(sock):
            env["YDOTOOL_SOCKET"] = sock
            break
    return env


class LinuxYdotoolInput:
    """Drive mouse/keyboard on Wayland through ``ydotool`` / ``ydotoold``."""

    def __init__(self, *, key_delay_ms: int = 12) -> None:
        self.key_delay_ms = key_delay_ms

    @staticmethod
    def available() -> tuple[bool, str]:
        if shutil.which("ydotool") is None:
            return False, "ydotool not installed"
        return True, "ydotool available"

    @staticmethod
    def can_type() -> bool:
        if shutil.which("ydotool") is None:
            return False
        import os

        # Allow explicit opt-in via env var for Wayland hosts where ydotoold
        # typing works (e.g. Sway/Hyprland).  On GNOME Wayland keyboard injection
        # via uinput is often ignored by the compositor, so default to False.
        if os.environ.get("VDISPLAY_ALLOW_YDOTOOL_TYPING") == "1":
            pass  # skip Wayland guard
        else:
            from vdisplay.capture.linux_xwd import _is_wayland_session

            if _is_wayland_session():
                return False
        if not os.access("/dev/uinput", os.W_OK):
            return False
        # probe daemon via socket (ydotoold default socket)
        for sock in ("/tmp/.ydotool_socket", os.path.expanduser("~/.ydotool_socket")):
            if os.path.exists(sock):
                return True
        # fallback: check if ydotoold process is alive
        try:
            import subprocess

            subprocess.run(
                ["pgrep", "-x", "ydotoold"],
                capture_output=True,
                check=True,
            )
            return True
        except Exception:
            return False

    @staticmethod
    def can_paste() -> bool:
        if shutil.which("ydotool") is None:
            return False
        # ydotoold may be able to inject hotkeys (Ctrl+V) even when GNOME
        # ignores ordinary keystrokes from uinput.
        for sock in ("/tmp/.ydotool_socket", os.path.expanduser("~/.ydotool_socket")):
            if os.path.exists(sock):
                return True
        try:
            import subprocess

            subprocess.run(
                ["pgrep", "-x", "ydotoold"],
                capture_output=True,
                check=True,
            )
            return True
        except Exception:
            return False

    def move(self, x: int, y: int) -> None:
        require_command("ydotool")
        run_command(
            ["ydotool", "mousemove", str(int(x)), str(int(y))],
            text=True,
            env=_ydotool_env(),
        )

    def click(self, button: int = 1) -> None:
        require_command("ydotool")
        run_command(
            ["ydotool", "click", f"0x{int(button):02x}"],
            text=True,
            env=_ydotool_env(),
        )

    def type_text(self, text: str) -> None:
        require_command("ydotool")
        run_command(
            ["ydotool", "type", "--key-delay", str(self.key_delay_ms), "--", text],
            text=True,
            env=_ydotool_env(),
        )

    def hotkey(self, *keys: str) -> None:
        require_command("ydotool")
        run_command(["ydotool", "key", *keys], text=True, env=_ydotool_env())
