from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass

from ..exceptions import BackendNotAvailableError, CapabilityError, VDisplayError
from ..models import Capabilities, SessionInfo
from ..utils import require_command, run_command
from .base import BaseBackend


@dataclass
class WindowState:
    window_id: str
    title: str
    x: int
    y: int
    width: int
    height: int


class LinuxX11RelayBackend(BaseBackend):
    """Move windows between monitors/outputs within the same X11 session."""

    name = "linux-x11-relay"

    def __init__(self, display: str | None = None, stash_prefix: str = "__vdisplay_stash__") -> None:
        super().__init__()
        self.display = display or os.environ.get("DISPLAY", ":0")
        self.stash_prefix = stash_prefix
        self._adopted: dict[str, WindowState] = {}

    def capabilities(self) -> Capabilities:
        return Capabilities(
            capture=False,
            input_control=True,
            window_adopt=True,
            isolation=False,
        )

    def info(self) -> SessionInfo:
        return SessionInfo(
            kind="relay",
            backend=self.name,
            active=self._active,
            metadata={
                "display": self.display,
                "adopted_windows": len(self._adopted),
            },
        )

    def start(self) -> None:
        if shutil.which("xdotool") is None:
            raise BackendNotAvailableError("xdotool is not installed")
        self._active = True

    def adopt_window(
        self,
        *,
        match_title: str | None = None,
        window_id: str | None = None,
        target: str = "offscreen",
    ) -> str:
        if not self._active:
            raise CapabilityError("Relay session is not active")

        wid = window_id or _find_window_id(self.display, match_title)
        geometry = _window_geometry(self.display, wid)
        title = _window_title(self.display, wid)
        key = wid

        if target == "offscreen":
            x, y = _offscreen_coordinates(self.display)
        else:
            x, y = _output_origin(self.display, target)

        run_command(
            ["xdotool", "windowmove", wid, str(x), str(y)],
            env={"DISPLAY": self.display},
            text=True,
        )

        self._adopted[key] = WindowState(
            window_id=wid,
            title=title,
            x=geometry[0],
            y=geometry[1],
            width=geometry[2],
            height=geometry[3],
        )
        return wid

    def release_window(
        self,
        *,
        match_title: str | None = None,
        window_id: str | None = None,
    ) -> str:
        if not self._active:
            raise CapabilityError("Relay session is not active")

        wid = window_id
        if wid is None and match_title:
            for state in self._adopted.values():
                if match_title.lower() in state.title.lower():
                    wid = state.window_id
                    break
        if wid is None:
            wid = _find_window_id(self.display, match_title)

        state = self._adopted.get(wid)
        if state is None:
            raise VDisplayError(f"Window {wid} was not adopted by this relay session")

        run_command(
            ["xdotool", "windowmove", wid, str(state.x), str(state.y)],
            env={"DISPLAY": self.display},
            text=True,
        )
        run_command(
            ["xdotool", "windowsize", wid, str(state.width), str(state.height)],
            env={"DISPLAY": self.display},
            text=True,
        )
        del self._adopted[wid]
        return wid

    def list_adopted(self) -> list[dict[str, str | int]]:
        return [
            {
                "window_id": s.window_id,
                "title": s.title,
                "x": s.x,
                "y": s.y,
                "width": s.width,
                "height": s.height,
            }
            for s in self._adopted.values()
        ]


def _find_window_id(display: str, match_title: str | None) -> str:
    require_command("xdotool")
    if not match_title:
        raise VDisplayError("match_title or window_id is required")

    result = run_command(
        ["xdotool", "search", "--name", match_title],
        env={"DISPLAY": display},
        text=True,
        check=False,
    )
    ids = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not ids:
        raise VDisplayError(f"No window matched title: {match_title}")
    return ids[-1]


def _window_geometry(display: str, window_id: str) -> tuple[int, int, int, int]:
    result = run_command(
        ["xdotool", "getwindowgeometry", "--shell", window_id],
        env={"DISPLAY": display},
        text=True,
    )
    values: dict[str, int] = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, raw = line.split("=", 1)
            if key in {"X", "Y", "WIDTH", "HEIGHT"}:
                values[key] = int(raw)
    return values["X"], values["Y"], values["WIDTH"], values["HEIGHT"]


def _window_title(display: str, window_id: str) -> str:
    result = run_command(
        ["xdotool", "getwindowname", window_id],
        env={"DISPLAY": display},
        text=True,
        check=False,
    )
    return result.stdout.strip()


def _offscreen_coordinates(display: str) -> tuple[int, int]:
    geometry = _screen_geometry(display)
    return geometry["width"] + 100, 100


def _screen_geometry(display: str) -> dict[str, int]:
    result = run_command(
        ["xdotool", "getdisplaygeometry"],
        env={"DISPLAY": display},
        text=True,
    )
    parts = result.stdout.strip().split()
    if len(parts) != 2:
        raise VDisplayError("Could not read display geometry")
    return {"width": int(parts[0]), "height": int(parts[1])}


def _output_origin(display: str, target: str) -> tuple[int, int]:
    if shutil.which("xrandr") is None:
        return _offscreen_coordinates(display)

    result = run_command(["xrandr", "--query"], env={"DISPLAY": display}, text=True)
    outputs = [
        match.group(1)
        for line in result.stdout.splitlines()
        if (match := re.match(r"^(\S+)\s+connected", line))
    ]
    resolved = target
    if target.lower() in {"primary", "default"} and outputs:
        resolved = outputs[0]
    elif target.lower().startswith("virtual:"):
        index = int(target.split(":", 1)[1]) - 1
        if 0 <= index < len(outputs):
            resolved = outputs[index]

    for line in result.stdout.splitlines():
        if not line.startswith(resolved + " "):
            continue
        match = re.search(r"(\d+)x(\d+)\+(\d+)\+(\d+)", line)
        if match:
            return int(match.group(3)), int(match.group(4))
    return _offscreen_coordinates(display)
