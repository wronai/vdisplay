from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from ..discovery import find_window_suggestions, resolve_host_display
from ..nl import describe_window_nl
from ..windows import (
    _matches_app,
    _matches_title,
    find_companion_frames,
    find_windows,
    pick_best_window,
)
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
    app_label: str = ""
    pid: int | None = None
    wm_class: str | None = None


class LinuxX11RelayBackend(BaseBackend):
    """Move windows between monitors/outputs within the same X11 session."""

    name = "linux-x11-relay"

    def __init__(self, display: str | None = None, stash_prefix: str = "__vdisplay_stash__") -> None:
        super().__init__()
        self.display = resolve_host_display(display)
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
        self._adopted = _load_stash(self.display, self.stash_prefix)
        self._active = True

    def adopt_window(
        self,
        *,
        match_title: str | None = None,
        window_id: str | None = None,
        match_class: str | None = None,
        match_pid: int | None = None,
        match_app: str | None = None,
        target: str = "offscreen",
    ) -> str:
        if not self._active:
            raise CapabilityError("Relay session is not active")

        if window_id:
            wid = window_id
            meta = _window_metadata(self.display, wid)
        else:
            wid, meta = _find_window_id(
                self.display,
                match_title=match_title,
                match_class=match_class,
                match_pid=match_pid,
                match_app=match_app,
            )
        geometry = _window_geometry(self.display, wid)
        title = meta.get("title") or meta.get("name") or _window_title(self.display, wid)
        key = wid

        if target == "offscreen":
            x, y = _offscreen_coordinates(self.display)
        else:
            x, y = _output_origin(self.display, target)

        _move_window(self.display, wid, x, y)
        self._adopted[key] = WindowState(
            window_id=wid,
            title=title,
            x=geometry[0],
            y=geometry[1],
            width=geometry[2],
            height=geometry[3],
            app_label=str(meta.get("app_label") or ""),
            pid=meta.get("pid"),
            wm_class=meta.get("wm_class"),
        )
        for frame in find_companion_frames(self.display, meta):
            frame_id = str(frame["window_id"])
            if frame_id in self._adopted:
                continue
            frame_geom = _window_geometry(self.display, frame_id)
            frame_title = frame.get("title") or frame.get("name") or ""
            _move_window(self.display, frame_id, x, y)
            self._adopted[frame_id] = WindowState(
                window_id=frame_id,
                title=frame_title,
                x=frame_geom[0],
                y=frame_geom[1],
                width=frame_geom[2],
                height=frame_geom[3],
                app_label=str(frame.get("app_label") or ""),
                pid=frame.get("pid"),
                wm_class=frame.get("wm_class"),
            )
        _save_stash(self.display, self.stash_prefix, self._adopted)
        return wid

    def release_window(
        self,
        *,
        match_title: str | None = None,
        window_id: str | None = None,
        match_class: str | None = None,
        match_pid: int | None = None,
        match_app: str | None = None,
    ) -> str:
        if not self._active:
            raise CapabilityError("Relay session is not active")

        if not any([window_id, match_title, match_class, match_pid is not None, match_app]):
            raise VDisplayError(
                "Provide --title, --class, --pid, --app or --window-id. "
                "Run: vdisplay relay list-windows --apps-only"
            )

        to_release = _select_adopted_for_release(
            self._adopted,
            window_id=window_id,
            match_title=match_title,
            match_class=match_class,
            match_pid=match_pid,
            match_app=match_app,
        )
        if not to_release:
            if window_id:
                raise VDisplayError(
                    f"Window {window_id} was not adopted by this relay session. "
                    "Run: vdisplay relay list"
                )
            wid, _meta = _find_window_id(
                self.display,
                match_title=match_title,
                match_class=match_class,
                match_pid=match_pid,
                match_app=match_app,
            )
            raise VDisplayError(
                f"Window {wid} is visible but was not adopted by this relay session. "
                "Run: vdisplay relay list"
            )

        primary = _pick_primary_release_id(self._adopted, to_release)
        for wid in to_release:
            state = self._adopted[wid]
            _restore_window(self.display, state)
            del self._adopted[wid]
        _save_stash(self.display, self.stash_prefix, self._adopted)
        return primary

    def list_adopted(self) -> list[dict[str, str | int | None]]:
        adopted: list[dict[str, str | int | None]] = []
        for state in self._adopted.values():
            info = {
                "window_id": state.window_id,
                "title": state.title,
                "app_label": state.app_label,
                "pid": state.pid,
                "wm_class": state.wm_class,
                "x": state.x,
                "y": state.y,
                "width": state.width,
                "height": state.height,
                "type": "frame" if state.wm_class == "mutter-x11-frames" else "application",
            }
            info["nl"] = describe_window_nl(info)
            adopted.append(info)
        return adopted


def _stash_path(display: str, stash_prefix: str) -> Path:
    safe_display = display.lstrip(":").replace("/", "_") or "0"
    cache = Path.home() / ".cache" / "vdisplay"
    cache.mkdir(parents=True, exist_ok=True)
    return cache / f"{stash_prefix}-{safe_display}.json"


def _load_stash(display: str, stash_prefix: str) -> dict[str, WindowState]:
    path = _stash_path(display, stash_prefix)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}
    adopted: dict[str, WindowState] = {}
    for wid, raw in payload.items():
        if isinstance(raw, dict):
            adopted[str(wid)] = WindowState(**raw)
    return adopted


def _save_stash(display: str, stash_prefix: str, adopted: dict[str, WindowState]) -> None:
    path = _stash_path(display, stash_prefix)
    if not adopted:
        if path.exists():
            path.unlink()
        return
    path.write_text(json.dumps({wid: asdict(state) for wid, state in adopted.items()}, indent=2))


def _state_as_match_info(state: WindowState) -> dict[str, object]:
    return {
        "app_label": state.app_label,
        "title": state.title,
        "name": state.title,
        "wm_class": state.wm_class,
        "wm_class_instance": state.wm_class,
        "pid": state.pid,
        "process_name": "",
    }


def _state_matches(
    state: WindowState,
    *,
    match_title: str | None = None,
    match_class: str | None = None,
    match_pid: int | None = None,
    match_app: str | None = None,
) -> bool:
    info = _state_as_match_info(state)
    if match_pid is not None and state.pid != match_pid:
        return False
    if match_class and not (
        state.wm_class and match_class.lower() in str(state.wm_class).lower()
    ):
        return False
    if match_app and not _matches_app(info, match_app):
        return False
    if match_title and not _matches_title(info, match_title):
        return False
    return True


def _select_adopted_for_release(
    adopted: dict[str, WindowState],
    *,
    window_id: str | None = None,
    match_title: str | None = None,
    match_class: str | None = None,
    match_pid: int | None = None,
    match_app: str | None = None,
) -> list[str]:
    if window_id:
        if window_id not in adopted:
            return []
        return _related_adopted_ids(adopted, window_id)

    matched = [
        wid
        for wid, state in adopted.items()
        if _state_matches(
            state,
            match_title=match_title,
            match_class=match_class,
            match_pid=match_pid,
            match_app=match_app,
        )
    ]
    if not matched:
        return []

    release_ids: set[str] = set()
    for wid in matched:
        release_ids.update(_related_adopted_ids(adopted, wid))
    return list(release_ids)


def _related_adopted_ids(adopted: dict[str, WindowState], seed_id: str) -> list[str]:
    state = adopted.get(seed_id)
    if state is None:
        return []
    label = str(state.app_label or "").strip().lower()
    if not label:
        return [seed_id]
    return [
        wid
        for wid, candidate in adopted.items()
        if str(candidate.app_label or "").strip().lower() == label
    ]


def _pick_primary_release_id(adopted: dict[str, WindowState], window_ids: list[str]) -> str:
    for wid in window_ids:
        state = adopted.get(wid)
        if state and state.wm_class != "mutter-x11-frames":
            return wid
    return window_ids[0]


def _restore_window(display: str, state: WindowState) -> None:
    run_command(
        ["xdotool", "windowmove", state.window_id, str(state.x), str(state.y)],
        env={"DISPLAY": display},
        text=True,
    )
    run_command(
        ["xdotool", "windowsize", state.window_id, str(state.width), str(state.height)],
        env={"DISPLAY": display},
        text=True,
    )


def _find_window_id(
    display: str,
    *,
    match_title: str | None = None,
    match_class: str | None = None,
    match_pid: int | None = None,
    match_app: str | None = None,
) -> tuple[str, dict]:
    if not any([match_title, match_class, match_pid is not None, match_app]):
        raise VDisplayError(
            "Provide --title, --class, --pid, --app or --window-id. "
            "Run: vdisplay relay list-windows --apps-only"
        )

    matches = find_windows(
        display,
        match_title=match_title,
        match_class=match_class,
        match_pid=match_pid,
        match_app=match_app,
        apps_only=True,
    )
    best = pick_best_window(matches)
    if best is None:
        suggestions = find_window_suggestions(display, match_title or match_app or match_class or "")
        hint = "No window matched"
        if match_title:
            hint += f" title={match_title!r}"
        if match_class:
            hint += f" class={match_class!r}"
        if match_pid is not None:
            hint += f" pid={match_pid}"
        if match_app:
            hint += f" app={match_app!r}"
        hint += ". Run: vdisplay relay list-windows --apps-only"
        if suggestions:
            labels = ", ".join(
                f"{s.get('app_label')!r} (pid={s.get('pid')}, id={s.get('window_id')})"
                for s in suggestions[:5]
            )
            hint += f". Suggestions: {labels}"
        raise VDisplayError(hint)
    return str(best["window_id"]), best


def _move_window(display: str, window_id: str, x: int, y: int) -> list[str]:
    run_command(
        ["xdotool", "windowmove", window_id, str(x), str(y)],
        env={"DISPLAY": display},
        text=True,
    )
    return [window_id]


def _window_metadata(display: str, window_id: str) -> dict:
    from ..windows import inspect_window

    return inspect_window(display, window_id)


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
