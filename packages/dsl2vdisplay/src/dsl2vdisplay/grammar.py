from __future__ import annotations

import shlex
from collections.abc import Callable
from typing import Any


def split_command(line: str) -> list[str]:
    line = line.strip()
    if not line or line.startswith("#"):
        return []
    try:
        return shlex.split(line, posix=True)
    except ValueError:
        return line.split()


def pick_flag(tokens: list[str], flag: str) -> str | None:
    if flag in tokens:
        idx = tokens.index(flag)
        if idx + 1 < len(tokens):
            return tokens[idx + 1]
    return None


def _with_display(rest: list[str], cmd: dict[str, Any]) -> dict[str, Any]:
    if d := pick_flag(rest, "DISPLAY"):
        cmd["display"] = d
    return cmd


def _parse_windows(rest: list[str], cmd: dict[str, Any]) -> dict[str, Any]:
    _with_display(rest, cmd)
    if "APPS_ONLY" in rest:
        cmd["apps_only"] = True
    if a := pick_flag(rest, "APP"):
        cmd["app"] = a
    return cmd


def _parse_screenshot(rest: list[str], cmd: dict[str, Any]) -> dict[str, Any]:
    if f := pick_flag(rest, "OUT"):
        cmd["out"] = f
    if d := pick_flag(rest, "DISPLAY"):
        cmd["display"] = d
    if w := pick_flag(rest, "WIDTH"):
        cmd["width"] = int(w)
    if h := pick_flag(rest, "HEIGHT"):
        cmd["height"] = int(h)
    return cmd


def _parse_virtual_start(rest: list[str], cmd: dict[str, Any]) -> dict[str, Any]:
    if d := pick_flag(rest, "DISPLAY"):
        cmd["display"] = d
    if w := pick_flag(rest, "WIDTH"):
        cmd["width"] = int(w)
    if h := pick_flag(rest, "HEIGHT"):
        cmd["height"] = int(h)
    return cmd


def _parse_launch(rest: list[str], cmd: dict[str, Any]) -> dict[str, Any]:
    if d := pick_flag(rest, "DISPLAY"):
        cmd["display"] = d
    launch = []
    for tok in rest:
        if tok in {"DISPLAY", "WIDTH", "HEIGHT"}:
            break
        if tok not in {cmd.get("display"), str(cmd.get("width")), str(cmd.get("height"))}:
            launch.append(tok)
    cmd["command"] = launch
    return cmd


def _parse_mirror(rest: list[str], cmd: dict[str, Any]) -> dict[str, Any]:
    if s := pick_flag(rest, "SOURCE"):
        cmd["source"] = s
    if t := pick_flag(rest, "TARGET"):
        cmd["target"] = t
    if d := pick_flag(rest, "DISPLAY"):
        cmd["display"] = d
    if f := pick_flag(rest, "OUT"):
        cmd["out"] = f
    return cmd


def _parse_adopt(rest: list[str], cmd: dict[str, Any]) -> dict[str, Any]:
    if t := pick_flag(rest, "TITLE"):
        cmd["title"] = t
    if w := pick_flag(rest, "WINDOW_ID"):
        cmd["window_id"] = w
    if tg := pick_flag(rest, "TARGET"):
        cmd["target"] = tg
    if d := pick_flag(rest, "DISPLAY"):
        cmd["display"] = d
    if a := pick_flag(rest, "APP"):
        cmd["app"] = a
    return cmd


def _parse_release(rest: list[str], cmd: dict[str, Any]) -> dict[str, Any]:
    if t := pick_flag(rest, "TITLE"):
        cmd["title"] = t
    if w := pick_flag(rest, "WINDOW_ID"):
        cmd["window_id"] = w
    if a := pick_flag(rest, "APP"):
        cmd["app"] = a
    if d := pick_flag(rest, "DISPLAY"):
        cmd["display"] = d
    return cmd


_VERB_PARSERS: dict[str, Callable[[list[str], dict[str, Any]], dict[str, Any]]] = {
    "HEALTH": _with_display,
    "INFO": _with_display,
    "CAPABILITIES": _with_display,
    "OUTPUTS": _with_display,
    "MONITORS": _with_display,
    "ALL": _with_display,
    "WINDOWS": _parse_windows,
    "VALIDATE": _with_display,
    "SCREENSHOT": _parse_screenshot,
    "VIRTUAL_START": _parse_virtual_start,
    "VIRTUAL_STOP": _with_display,
    "LAUNCH": _parse_launch,
    "MIRROR": _parse_mirror,
    "ADOPT": _parse_adopt,
    "RELEASE": _parse_release,
}


def parse_line(line: str) -> dict[str, Any] | None:
    tokens = split_command(line)
    if not tokens:
        return None
    verb = tokens[0].upper()
    parser = _VERB_PARSERS.get(verb)
    if parser is None:
        return {"verb": verb}
    return parser(tokens[1:], {"verb": verb})


def to_text(cmd: dict[str, Any]) -> str:
    verb = str(cmd.get("verb", "")).upper()
    if verb == "INFO":
        return "INFO"
    if verb == "OUTPUTS":
        return f"OUTPUTS DISPLAY {cmd.get('display', ':0')}"
    if verb == "SCREENSHOT":
        parts = ["SCREENSHOT", f"OUT {cmd.get('out', 'screen.png')}"]
        if d := cmd.get("display"):
            parts.append(f"DISPLAY {d}")
        return " ".join(parts)
    if verb == "MIRROR":
        parts = ["MIRROR", f"SOURCE {cmd.get('source', 'primary')}"]
        if t := cmd.get("target"):
            parts.append(f"TARGET {t}")
        return " ".join(parts)
    return verb
