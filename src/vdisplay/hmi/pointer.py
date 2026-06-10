"""Desktop pointer probes for live HMI watch."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Any

from ..discovery import list_monitors, resolve_host_display

_GTK_LAST_ERROR: str | None = None
_GNOME_LAST_ERROR: str | None = None


def is_wayland_session() -> bool:
    if os.environ.get("WAYLAND_DISPLAY", "").strip():
        return True
    return os.environ.get("XDG_SESSION_TYPE", "").strip().lower() == "wayland"


def pointer_probe_errors() -> dict[str, str | None]:
    return {"gtk": _GTK_LAST_ERROR, "gnome": _GNOME_LAST_ERROR}


def _session_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in (
        "WAYLAND_DISPLAY",
        "XDG_RUNTIME_DIR",
        "DBUS_SESSION_BUS_ADDRESS",
        "DISPLAY",
        "XDG_SESSION_TYPE",
        "XDG_CURRENT_DESKTOP",
        "HOME",
    ):
        value = os.environ.get(key)
        if value:
            env[key] = value
    return env


@dataclass(frozen=True)
class PointerSample:
    x: int | None
    y: int | None
    window_id: str | None = None
    sources: dict[str, tuple[int, int]] = field(default_factory=dict)
    monitor: dict[str, Any] | None = None
    window_title: str | None = None
    error: str | None = None
    primary: str | None = None
    stale_sources: tuple[str, ...] = ()

    def primary_label(self) -> str:
        if self.x is None or self.y is None:
            stale = " ".join(
                f"{name}*=({xy[0]},{xy[1]})" for name, xy in sorted(self.sources.items()) if name in self.stale_sources
            )
            live = " ".join(
                f"{name}=({xy[0]},{xy[1]})" for name, xy in sorted(self.sources.items()) if name not in self.stale_sources
            )
            extra = " ".join(part for part in (live, stale) if part)
            return f"? [{extra}]" if extra else "?"

        label = self.primary or next(iter(self.sources), "ptr")
        parts = [f"{label}=({self.x},{self.y})"]
        others = [
            f"{name}=({xy[0]},{xy[1]})" + ("*" if name in self.stale_sources else "")
            for name, xy in sorted(self.sources.items())
            if name != label
        ]
        if others:
            parts.append("[" + " ".join(others) + "]")
        return " ".join(parts)


_GTK_POINTER_SCRIPT = """
import os
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, Gio

app = Gtk.Application(
    application_id="com.vdisplay.hmi.%d" % os.getpid(),
    flags=Gio.ApplicationFlags.NON_UNIQUE,
)

def on_activate(application):
    display = Gdk.Display.get_default()
    if display is None:
        print("ERR:no-display")
        application.quit()
        return
    _, x, y = display.get_default_seat().get_pointer().get_position()
    print("%d,%d" % (x, y))
    application.quit()

app.connect("activate", on_activate)
app.run([])
"""


def _parse_xdotool_shell(text: str) -> tuple[int, int, str | None]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key.strip().upper()] = value.strip()
    x = int(values["X"])
    y = int(values["Y"])
    window_id = values.get("WINDOW")
    return x, y, window_id


def probe_xdotool(*, display: str | None = None) -> tuple[int, int, str | None] | None:
    if shutil.which("xdotool") is None:
        return None
    env = _session_env()
    if display:
        env["DISPLAY"] = resolve_host_display(display)
    try:
        proc = subprocess.run(
            ["xdotool", "getmouselocation", "--shell"],
            capture_output=True,
            text=True,
            timeout=1.5,
            check=False,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        return _parse_xdotool_shell(proc.stdout)
    except (KeyError, TypeError, ValueError):
        return None


def probe_gnome_shell_pointer() -> tuple[int, int] | None:
    global _GNOME_LAST_ERROR
    if shutil.which("gdbus") is None:
        _GNOME_LAST_ERROR = "gdbus not on PATH"
        return None
    try:
        proc = subprocess.run(
            [
                "gdbus",
                "call",
                "--session",
                "--dest",
                "org.gnome.Shell",
                "--object-path",
                "/org/gnome/Shell",
                "--method",
                "org.gnome.Shell.Eval",
                "JSON.stringify(global.get_pointer())",
            ],
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
            env=_session_env(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        _GNOME_LAST_ERROR = str(exc)
        return None
    if proc.returncode != 0:
        _GNOME_LAST_ERROR = (proc.stderr or proc.stdout or "gdbus failed").strip()
        return None
    text = (proc.stdout or "").strip()
    match = re.search(r"\(\s*true\s*,\s*'([^']*)'\s*\)", text, flags=re.IGNORECASE)
    if not match:
        _GNOME_LAST_ERROR = f"gnome eval failed: {text or 'empty response'}"
        return None
    payload = match.group(1)
    try:
        parsed = json.loads(payload)
        if isinstance(parsed, list) and len(parsed) >= 2:
            return int(parsed[0]), int(parsed[1])
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    xy = re.fullmatch(r"(-?\d+)\s*,\s*(-?\d+)", payload)
    if xy:
        return int(xy.group(1)), int(xy.group(2))
    _GNOME_LAST_ERROR = f"unexpected gnome payload: {payload!r}"
    return None


def probe_gtk_subprocess(*, python: str = "/usr/bin/python3") -> tuple[int, int] | None:
    global _GTK_LAST_ERROR
    if not os.path.isfile(python):
        _GTK_LAST_ERROR = f"{python} missing"
        return None
    try:
        proc = subprocess.run(
            [python, "-c", _GTK_POINTER_SCRIPT],
            capture_output=True,
            text=True,
            timeout=3.0,
            check=False,
            env=_session_env(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        _GTK_LAST_ERROR = str(exc)
        return None
    line = (proc.stdout or "").strip().splitlines()[-1] if proc.stdout else ""
    if proc.returncode != 0 or line.startswith("ERR:"):
        err = (proc.stderr or proc.stdout or line or "gtk probe failed").strip().splitlines()
        _GTK_LAST_ERROR = err[-1] if err else "gtk probe failed"
        return None
    match = re.fullmatch(r"(-?\d+),(-?\d+)", line.strip())
    if not match:
        _GTK_LAST_ERROR = f"unexpected gtk output: {line!r}"
        return None
    _GTK_LAST_ERROR = None
    return int(match.group(1)), int(match.group(2))


def probe_absolute_pointer(*, display: str | None = None, use_gtk: bool = True) -> tuple[str, tuple[int, int]] | None:
    """Return the best absolute pointer source available on this session."""
    if is_wayland_session():
        gnome = probe_gnome_shell_pointer()
        if gnome is not None:
            return "gnome", gnome
        if use_gtk:
            gtk = probe_gtk_subprocess()
            if gtk is not None:
                return "gtk", gtk
    elif use_gtk:
        gtk = probe_gtk_subprocess()
        if gtk is not None:
            return "gtk", gtk
    xdotool = probe_xdotool(display=display)
    if xdotool is not None:
        return "xdotool", (xdotool[0], xdotool[1])
    return None


def _window_title(window_id: str | None, *, display: str | None = None) -> str | None:
    if not window_id or shutil.which("xdotool") is None:
        return None
    env = _session_env()
    if display:
        env["DISPLAY"] = resolve_host_display(display)
    try:
        proc = subprocess.run(
            ["xdotool", "getwindowname", window_id],
            capture_output=True,
            text=True,
            timeout=1.0,
            check=False,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    title = (proc.stdout or "").strip()
    return title or None


def monitor_at(x: int, y: int, *, display: str | None = None) -> dict[str, Any] | None:
    try:
        monitors = list_monitors(resolve_host_display(display))
    except Exception:
        return None
    for monitor in monitors:
        left = int(monitor.get("x") or 0)
        top = int(monitor.get("y") or 0)
        width = int(monitor.get("width") or 0)
        height = int(monitor.get("height") or 0)
        if width <= 0 or height <= 0:
            continue
        if left <= x < left + width and top <= y < top + height:
            return monitor
    return None


def _pick_primary(sources: dict[str, tuple[int, int]], *, wayland: bool) -> str | None:
    order = ("evdev", "gnome", "gtk", "xdotool") if wayland else ("xdotool", "gnome", "gtk", "evdev")
    for name in order:
        if name in sources:
            return name
    return next(iter(sources), None)


def _stale_sources(history: dict[str, list[tuple[int, int]]], *, min_samples: int = 6) -> tuple[str, ...]:
    stale: list[str] = []
    for name, samples in history.items():
        if len(samples) < min_samples:
            continue
        if len({sample for sample in samples[-min_samples:]}) == 1:
            stale.append(name)
    return tuple(stale)


def sample_pointer(
    *,
    display: str | None = None,
    use_gtk: bool = True,
    gtk_every: int = 1,
    tick: int = 0,
    evdev_xy: tuple[int, int] | None = None,
    evdev_relative_only: bool = False,
    source_history: dict[str, list[tuple[int, int]]] | None = None,
) -> PointerSample:
    sources: dict[str, tuple[int, int]] = {}
    window_id: str | None = None
    wayland = is_wayland_session()
    history = source_history if source_history is not None else {}

    if evdev_xy is not None:
        key = "evdev-rel" if evdev_relative_only else "evdev"
        sources[key] = evdev_xy
        history.setdefault(key, []).append(evdev_xy)

    if wayland and tick % max(1, gtk_every) == 0:
        gnome = probe_gnome_shell_pointer()
        if gnome is not None:
            sources["gnome"] = gnome
            history.setdefault("gnome", []).append(gnome)

    if use_gtk and tick % max(1, gtk_every) == 0:
        gtk = probe_gtk_subprocess()
        if gtk is not None:
            sources["gtk"] = gtk
            history.setdefault("gtk", []).append(gtk)

    xdotool = probe_xdotool(display=display)
    if xdotool is not None:
        sources["xdotool"] = (xdotool[0], xdotool[1])
        window_id = xdotool[2]
        history.setdefault("xdotool", []).append(sources["xdotool"])
        for name, samples in list(history.items()):
            if len(samples) > 24:
                history[name] = samples[-24:]

    if not sources:
        errors = pointer_probe_errors()
        hint = "no live pointer source"
        detail = "; ".join(f"{k}={v}" for k, v in errors.items() if v)
        return PointerSample(x=None, y=None, error=f"{hint} ({detail})" if detail else hint)

    stale = _stale_sources(history)
    live_sources = {name: xy for name, xy in sources.items() if name not in stale}
    primary = _pick_primary(live_sources or sources, wayland=wayland)
    if primary is None or (primary in stale and wayland):
        primary = _pick_primary(live_sources, wayland=wayland)

    if primary is None or primary in stale:
        err_bits = ["no live pointer on Wayland (xdotool is stale)"]
        if evdev_relative_only:
            err_bits.append("evdev-rel is movement-only until seeded by gnome/gtk")
        errors = pointer_probe_errors()
        detail = "; ".join(f"{k}={v}" for k, v in errors.items() if v)
        if detail:
            err_bits.append(detail)
        return PointerSample(
            x=None,
            y=None,
            window_id=window_id,
            sources=sources,
            primary=None,
            stale_sources=stale,
            error=" — ".join(err_bits),
        )

    x, y = sources[primary]
    monitor = monitor_at(x, y, display=display)
    title = _window_title(window_id, display=display)
    error = None
    if evdev_relative_only and primary.startswith("evdev"):
        error = "evdev-rel is relative motion, not absolute screen coords"
    return PointerSample(
        x=x,
        y=y,
        window_id=window_id,
        sources=sources,
        monitor=monitor,
        window_title=title,
        primary=primary,
        stale_sources=stale,
        error=error,
    )
