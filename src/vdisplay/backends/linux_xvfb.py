from __future__ import annotations

import os
import shutil
import subprocess
import time
from typing import Sequence

from ..capture.linux_xwd import capture_display_png
from ..exceptions import BackendNotAvailableError, CapabilityError
from ..models import Capabilities, SessionInfo
from .base import BaseBackend


class LinuxXvfbBackend(BaseBackend):
    name = "linux-xvfb"

    def __init__(self, width: int = 1920, height: int = 1080, display: str = ":99") -> None:
        super().__init__()
        self.width = width
        self.height = height
        self.display = display
        self.proc: subprocess.Popen | None = None

    def capabilities(self) -> Capabilities:
        return Capabilities(
            capture=True,
            input_control=True,
            launch=True,
            window_adopt=False,
            isolation=True,
        )

    def info(self) -> SessionInfo:
        return SessionInfo(
            kind="virtual",
            backend=self.name,
            active=self._active,
            width=self.width,
            height=self.height,
            metadata={"display": self.display},
        )

    def start(self) -> None:
        if shutil.which("Xvfb") is None:
            raise BackendNotAvailableError("Xvfb is not installed")
        if self._active:
            return
        self.proc = subprocess.Popen(
            ["Xvfb", self.display, "-screen", "0", f"{self.width}x{self.height}x24"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _wait_for_display(self.display)
        self._active = True

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            self.proc.wait(timeout=5)
        self.proc = None
        self._active = False

    def launch(self, command: Sequence[str]) -> int | None:
        if not self._active:
            raise CapabilityError("Display session is not active")
        env = os.environ.copy()
        env["DISPLAY"] = self.display
        proc = subprocess.Popen(list(command), env=env)
        return proc.pid

    def screenshot_bytes(self) -> bytes:
        if not self._active:
            raise CapabilityError("Display session is not active")
        return capture_display_png(self.display)

    def adopt_window(self, *, match_title: str | None = None, window_id: str | None = None) -> None:
        raise CapabilityError(
            "linux-xvfb cannot adopt windows from another X server; "
            "use launch() for new apps or WindowRelaySession for same-session monitor moves"
        )

    def release_window(self, *, match_title: str | None = None, window_id: str | None = None) -> None:
        raise CapabilityError("linux-xvfb does not track adopted windows")


def _wait_for_display(display: str, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        probe = subprocess.run(
            ["xwd", "-root", "-display", display],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if probe.returncode == 0:
            return
        time.sleep(0.1)
    raise BackendNotAvailableError(f"Display {display} did not become ready in time")
