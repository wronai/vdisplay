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


_MULTI_WORD_VERBS: dict[tuple[str, str], str] = {
    ("CONTROLS", "LIST"): "CONTROLS_LIST",
    ("CONTROLS", "FIND"): "CONTROLS_FIND",
    ("CONTROL", "CLICK"): "CONTROL_CLICK",
    ("CONTROL", "FOCUS"): "CONTROL_FOCUS",
    ("CONTROL", "SET_VALUE"): "CONTROL_SET_VALUE",
    ("CONTROL", "SETVALUE"): "CONTROL_SET_VALUE",
    ("DIAGNOSE", "CONTROL"): "DIAGNOSE_CONTROL",
    ("TERMINAL", "OPEN"): "TERMINAL_OPEN",
    ("BROWSER", "OPEN"): "BROWSER_OPEN",
}


def normalize_tokens(tokens: list[str]) -> list[str]:
    normalized: list[str] = []
    for token in tokens:
        if token.startswith("--"):
            normalized.append(token[2:].replace("-", "_").upper())
        else:
            normalized.append(token)
    return normalized


def resolve_verb(tokens: list[str]) -> tuple[str, list[str]]:
    tokens = normalize_tokens(tokens)
    if not tokens:
        return "", []
    first = tokens[0].upper()
    if len(tokens) >= 2:
        second = tokens[1].upper().replace("-", "_")
        mapped = _MULTI_WORD_VERBS.get((first, second))
        if mapped:
            return mapped, tokens[2:]
    return first, tokens[1:]


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


def _has_flag(tokens: list[str], flag: str) -> bool:
    return flag in tokens


def _parse_control_common(rest: list[str], cmd: dict[str, Any]) -> dict[str, Any]:
    _with_display(rest, cmd)
    
    string_flags = {
        "SELECTOR": "selector",
        "ROLE": "role",
        "NAME": "name",
        "APP": "app",
        "WINDOW_TITLE": "window_title",
        "WINDOW_ID": "window_id",
        "BACKEND": "control_backend",
        "VERIFY_LABEL": "verify_label",
        "VERIFY_SELECTOR": "verify_selector",
        "PROVIDER_REF": "provider_ref",
        "ENVIRONMENT": "environment",
        "TEXT": "text",
        "TEXT_CONTAINS": "text_contains",
        "SESSION_ID": "session_id",
    }

    for flag, key in string_flags.items():
        if val := pick_flag(rest, flag):
            cmd[key] = val

    if i := pick_flag(rest, "INDEX"):
        cmd["index"] = int(i)
    if line_no := pick_flag(rest, "TERMINAL_LINE"):
        cmd["terminal_line"] = int(line_no)
    if col_no := pick_flag(rest, "TERMINAL_COL"):
        cmd["terminal_col"] = int(col_no)
        
    for flag, key in [("VERIFY", "verify"), ("SCREENSHOT_VERIFY", "screenshot_verify")]:
        if _has_flag(rest, flag):
            cmd[key] = True

    if ref := pick_flag(rest, "ID"):
        cmd.setdefault("provider_ref", ref)
    return cmd


def _parse_controls_list(rest: list[str], cmd: dict[str, Any]) -> dict[str, Any]:
    _parse_control_common(rest, cmd)
    if d := pick_flag(rest, "MAX_DEPTH"):
        cmd["max_depth"] = int(d)
    if f := pick_flag(rest, "FORMAT"):
        cmd["format"] = f
    return cmd


def _parse_controls_find(rest: list[str], cmd: dict[str, Any]) -> dict[str, Any]:
    return _parse_control_common(rest, cmd)


def _parse_control_click(rest: list[str], cmd: dict[str, Any]) -> dict[str, Any]:
    return _parse_control_common(rest, cmd)


def _parse_control_focus(rest: list[str], cmd: dict[str, Any]) -> dict[str, Any]:
    return _parse_control_common(rest, cmd)


def _parse_control_set_value(rest: list[str], cmd: dict[str, Any]) -> dict[str, Any]:
    _parse_control_common(rest, cmd)
    if v := pick_flag(rest, "VALUE"):
        cmd["value"] = v
    return cmd


def _parse_diagnose_control(rest: list[str], cmd: dict[str, Any]) -> dict[str, Any]:
    return _with_display(rest, cmd)


def _parse_browser_open(rest: list[str], cmd: dict[str, Any]) -> dict[str, Any]:
    if sid := pick_flag(rest, "SESSION_ID") or pick_flag(rest, "SESSION"):
        cmd["session_id"] = sid
    if url := pick_flag(rest, "URL"):
        cmd["url"] = url
    if title := pick_flag(rest, "TITLE"):
        cmd["title"] = title
    if vendor := pick_flag(rest, "VENDOR"):
        cmd["vendor"] = vendor
    elif engine := pick_flag(rest, "ENGINE"):
        cmd["engine"] = engine
    if profile := pick_flag(rest, "PROFILE"):
        cmd["profile"] = profile
    if "HEADED" in rest or "NO_HEADLESS" in rest:
        cmd["headless"] = False
    elif headless := pick_flag(rest, "HEADLESS"):
        cmd["headless"] = str(headless).lower() in {"1", "true", "yes"}
    return cmd


def _parse_terminal_open(rest: list[str], cmd: dict[str, Any]) -> dict[str, Any]:
    if sid := pick_flag(rest, "SESSION_ID"):
        cmd["session_id"] = sid
    if command := pick_flag(rest, "COMMAND"):
        cmd["command"] = command
    if rows := pick_flag(rest, "ROWS"):
        cmd["rows"] = int(rows)
    if cols := pick_flag(rest, "COLS"):
        cmd["cols"] = int(cols)
    if title := pick_flag(rest, "TITLE"):
        cmd["title"] = title
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
    "CONTROLS_LIST": _parse_controls_list,
    "CONTROLS_FIND": _parse_controls_find,
    "CONTROL_CLICK": _parse_control_click,
    "CONTROL_FOCUS": _parse_control_focus,
    "CONTROL_SET_VALUE": _parse_control_set_value,
    "DIAGNOSE_CONTROL": _parse_diagnose_control,
    "TERMINAL_OPEN": _parse_terminal_open,
    "BROWSER_OPEN": _parse_browser_open,
}


def parse_line(line: str) -> dict[str, Any] | None:
    tokens = split_command(line)
    if not tokens:
        return None
    verb, rest = resolve_verb(tokens)
    parser = _VERB_PARSERS.get(verb)
    if parser is None:
        return {"verb": verb}
    return parser(rest, {"verb": verb})


def _screenshot_to_text(cmd: dict[str, Any]) -> str:
    parts = ["SCREENSHOT", f"OUT {cmd.get('out', 'screen.png')}"]
    if d := cmd.get("display"):
        parts.append(f"DISPLAY {d}")
    return " ".join(parts)


def _mirror_to_text(cmd: dict[str, Any]) -> str:
    parts = ["MIRROR", f"SOURCE {cmd.get('source', 'primary')}"]
    if t := cmd.get("target"):
        parts.append(f"TARGET {t}")
    return " ".join(parts)


def _controls_list_to_text(cmd: dict[str, Any]) -> str:
    parts = ["controls", "list"]
    if a := cmd.get("app"):
        parts.extend(["--app", f'"{a}"'])
    if b := cmd.get("control_backend"):
        parts.extend(["--backend", b])
    return " ".join(parts)


_TEXT_FORMATTERS: dict[str, Callable[[dict[str, Any]], str]] = {
    "INFO": lambda c: "INFO",
    "OUTPUTS": lambda c: f"OUTPUTS DISPLAY {c.get('display', ':0')}",
    "SCREENSHOT": _screenshot_to_text,
    "MIRROR": _mirror_to_text,
    "CONTROLS_LIST": _controls_list_to_text,
    "CONTROLS_FIND": lambda c: _control_to_text("find", c),
    "CONTROL_CLICK": lambda c: _control_to_text("click", c),
    "CONTROL_FOCUS": lambda c: _control_to_text("focus", c),
    "CONTROL_SET_VALUE": lambda c: _control_to_text("set-value", c),
    "DIAGNOSE_CONTROL": lambda c: "diagnose control",
    "TERMINAL_OPEN": lambda c: _terminal_open_to_text(c),
    "BROWSER_OPEN": lambda c: _browser_open_to_text(c),
}


def _browser_open_to_text(cmd: dict[str, Any]) -> str:
    parts = ["browser", "open"]
    for key, flag in (
        ("session_id", "--session"),
        ("url", "--url"),
        ("title", "--title"),
    ):
        if value := cmd.get(key):
            parts.extend([flag, f'"{value}"' if " " in str(value) else str(value)])
    if vendor := cmd.get("vendor"):
        parts.extend(["--vendor", str(vendor)])
    elif engine := cmd.get("engine"):
        parts.extend(["--engine", str(engine)])
    elif profile := cmd.get("profile"):
        parts.extend(["--profile", str(profile)])
    if cmd.get("headless") is False:
        parts.append("--headed")
    return " ".join(parts)


def _terminal_open_to_text(cmd: dict[str, Any]) -> str:
    parts = ["terminal", "open"]
    for key, flag in (
        ("session_id", "--session-id"),
        ("command", "--command"),
        ("title", "--title"),
    ):
        if value := cmd.get(key):
            parts.extend([flag, f'"{value}"' if " " in str(value) else str(value)])
    if rows := cmd.get("rows"):
        parts.extend(["--rows", str(rows)])
    if cols := cmd.get("cols"):
        parts.extend(["--cols", str(cols)])
    return " ".join(parts)


def to_text(cmd: dict[str, Any]) -> str:
    verb = str(cmd.get("verb", "")).upper()
    if formatter := _TEXT_FORMATTERS.get(verb):
        return formatter(cmd)
    return verb


def _control_to_text(action: str, cmd: dict[str, Any]) -> str:
    parts = ["control", action]
    for key, flag in (
        ("selector", "--selector"),
        ("role", "--role"),
        ("name", "--name"),
        ("app", "--app"),
        ("window_title", "--window-title"),
        ("provider_ref", "--provider-ref"),
        ("value", "--value"),
        ("control_backend", "--backend"),
        ("environment", "--environment"),
        ("text", "--text"),
        ("text_contains", "--text-contains"),
        ("session_id", "--session-id"),
    ):
        if value := cmd.get(key):
            parts.extend([flag, f'"{value}"' if " " in str(value) else str(value)])
    if line_no := cmd.get("terminal_line"):
        parts.extend(["--terminal-line", str(line_no)])
    if col_no := cmd.get("terminal_col"):
        parts.extend(["--terminal-col", str(col_no)])
    if cmd.get("verify"):
        parts.append("--verify")
    if cmd.get("screenshot_verify"):
        parts.append("--screenshot-verify")
    return " ".join(parts)
