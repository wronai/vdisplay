from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path
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
        self._owns_display = False

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
            metadata={"display": self.display, "owns_display": self._owns_display},
        )

    def start(self) -> None:
        if shutil.which("Xvfb") is None:
            raise BackendNotAvailableError("Xvfb is not installed")
        if shutil.which("xwd") is None:
            raise BackendNotAvailableError(
                "xwd is not installed (package: x11-apps). "
                "Install: sudo apt install x11-apps"
            )
        if self._active:
            return

        display = self._acquire_display(self.display)
        self.display = display
        _wait_for_display(self.display, proc=self.proc)
        self._active = True

    def stop(self) -> None:
        if self._owns_display and self.proc and self.proc.poll() is None:
            self.proc.terminate()
            self.proc.wait(timeout=5)
        self.proc = None
        self._owns_display = False
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

    def _acquire_display(self, preferred: str) -> str:
        if _probe_display(preferred):
            self._owns_display = False
            self.proc = None
            return preferred

        for candidate in _display_candidates(preferred):
            if _display_socket_exists(candidate) and not _probe_display(candidate):
                continue
            proc = subprocess.Popen(
                ["Xvfb", candidate, "-screen", "0", f"{self.width}x{self.height}x24"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            time.sleep(0.2)
            if proc.poll() is not None:
                err = (proc.stderr.read() if proc.stderr else b"").decode("utf-8", errors="replace").strip()
                continue
            if _probe_display(candidate):
                self.proc = proc
                self._owns_display = True
                return candidate
            proc.terminate()
            proc.wait(timeout=2)

        raise BackendNotAvailableError(
            f"Could not start Xvfb virtual display (tried {preferred} and alternates). "
            "Check: which Xvfb xwd; free display with: pkill -f 'Xvfb :99'"
        )


def _display_candidates(preferred: str) -> list[str]:
    if preferred.startswith(":") and preferred[1:].isdigit():
        base = int(preferred[1:])
        return [f":{n}" for n in range(base, base + 10)]
    return [preferred, ":99", ":100", ":101"]


def _display_socket_exists(display: str) -> bool:
    return Path(f"/tmp/.X11-unix/X{display.lstrip(':')}").exists()


def _probe_display(display: str) -> bool:
    if shutil.which("xwd") is None:
        return False
    probe = subprocess.run(
        ["xwd", "-root", "-display", display],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=5,
    )
    return probe.returncode == 0


def _wait_for_display(display: str, *, proc: subprocess.Popen | None, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    last_error = "xwd probe failed"
    while time.monotonic() < deadline:
        if proc is not None and proc.poll() is not None:
            err = ""
            if proc.stderr:
                err = proc.stderr.read().decode("utf-8", errors="replace").strip()
            raise BackendNotAvailableError(
                f"Xvfb exited on {display}" + (f": {err}" if err else "")
            )
        if _probe_display(display):
            return
        time.sleep(0.1)
    raise BackendNotAvailableError(
        f"Display {display} did not become ready in {timeout}s. "
        "Ensure x11-apps (xwd) is installed."
    )
