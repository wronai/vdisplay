from __future__ import annotations

import shlex
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


def parse_line(line: str) -> dict[str, Any] | None:
    tokens = split_command(line)
    if not tokens:
        return None
    verb = tokens[0].upper()
    rest = tokens[1:]
    cmd: dict[str, Any] = {"verb": verb}

    if verb in {"HEALTH", "INFO", "CAPABILITIES"}:
        if d := pick_flag(rest, "DISPLAY"):
            cmd["display"] = d
    elif verb == "OUTPUTS":
        if d := pick_flag(rest, "DISPLAY"):
            cmd["display"] = d
    elif verb == "WINDOWS":
        if d := pick_flag(rest, "DISPLAY"):
            cmd["display"] = d
    elif verb == "VALIDATE":
        if d := pick_flag(rest, "DISPLAY"):
            cmd["display"] = d
    elif verb == "SCREENSHOT":
        if f := pick_flag(rest, "OUT"):
            cmd["out"] = f
        if d := pick_flag(rest, "DISPLAY"):
            cmd["display"] = d
        if w := pick_flag(rest, "WIDTH"):
            cmd["width"] = int(w)
        if h := pick_flag(rest, "HEIGHT"):
            cmd["height"] = int(h)
    elif verb == "VIRTUAL_START":
        if d := pick_flag(rest, "DISPLAY"):
            cmd["display"] = d
        if w := pick_flag(rest, "WIDTH"):
            cmd["width"] = int(w)
        if h := pick_flag(rest, "HEIGHT"):
            cmd["height"] = int(h)
    elif verb == "VIRTUAL_STOP":
        if d := pick_flag(rest, "DISPLAY"):
            cmd["display"] = d
    elif verb == "LAUNCH":
        if d := pick_flag(rest, "DISPLAY"):
            cmd["display"] = d
        launch = []
        for tok in rest:
            if tok in {"DISPLAY", "WIDTH", "HEIGHT"}:
                break
            if tok not in {cmd.get("display"), str(cmd.get("width")), str(cmd.get("height"))}:
                launch.append(tok)
        cmd["command"] = launch
    elif verb == "MIRROR":
        if s := pick_flag(rest, "SOURCE"):
            cmd["source"] = s
        if t := pick_flag(rest, "TARGET"):
            cmd["target"] = t
        if d := pick_flag(rest, "DISPLAY"):
            cmd["display"] = d
        if f := pick_flag(rest, "OUT"):
            cmd["out"] = f
    elif verb == "ADOPT":
        if t := pick_flag(rest, "TITLE"):
            cmd["title"] = t
        if w := pick_flag(rest, "WINDOW_ID"):
            cmd["window_id"] = w
        if tg := pick_flag(rest, "TARGET"):
            cmd["target"] = tg
        if d := pick_flag(rest, "DISPLAY"):
            cmd["display"] = d
    elif verb == "RELEASE":
        if t := pick_flag(rest, "TITLE"):
            cmd["title"] = t
        if w := pick_flag(rest, "WINDOW_ID"):
            cmd["window_id"] = w
        if d := pick_flag(rest, "DISPLAY"):
            cmd["display"] = d
    else:
        return None
    return cmd


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
