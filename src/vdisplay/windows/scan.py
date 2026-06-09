from __future__ import annotations

import re
import shutil
from typing import Any

from ..utils import run_command


def root_window_id(display: str) -> str:
    if shutil.which("xwininfo") is None:
        return ""
    result = run_command(["xwininfo", "-root"], env={"DISPLAY": display}, text=True, check=False)
    match = re.search(r"Window id:\s*(0x[0-9a-fA-F]+)", result.stdout)
    if not match:
        return ""
    return str(int(match.group(1), 16))


def xdotool(display: str, *args: str) -> str:
    result = run_command(["xdotool", *args], env={"DISPLAY": display}, text=True, check=False)
    return result.stdout


def format_window_id(window_id: str) -> str:
    if window_id.startswith("0x"):
        return window_id
    try:
        return hex(int(window_id))
    except ValueError:
        return window_id


def xprop(display: str, window_id: str) -> dict[str, str]:
    if shutil.which("xprop") is None:
        return {}
    wid = format_window_id(window_id)
    result = run_command(
        [
            "xprop",
            "-id",
            wid,
            "WM_CLASS",
            "WM_NAME",
            "_NET_WM_NAME",
            "_NET_WM_PID",
            "_NET_WM_WINDOW_TYPE",
        ],
        env={"DISPLAY": display},
        text=True,
        check=False,
    )
    props: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if "=" not in line:
            continue
        key, raw = line.split("=", 1)
        key = key.strip().split("(", 1)[0]
        raw = raw.strip()
        if raw.endswith(","):
            raw = raw[:-1].strip()
        props[key] = decode_xprop_value(raw)
    return props


def decode_xprop_value(raw: str) -> str:
    raw = raw.strip()
    if not raw or raw == '""':
        return ""
    parts = re.findall(r'"([^"]*)"', raw)
    if parts:
        return ", ".join(parts)
    if raw.startswith("(") and raw.endswith(")"):
        return raw[1:-1].strip()
    return raw


def window_geometry(display: str, window_id: str) -> dict[str, int]:
    result = run_command(
        ["xdotool", "getwindowgeometry", "--shell", window_id],
        env={"DISPLAY": display},
        text=True,
        check=False,
    )
    values: dict[str, int] = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, raw = line.split("=", 1)
            if key in {"X", "Y", "WIDTH", "HEIGHT"}:
                values[key] = int(raw)
    return {
        "x": values.get("X", 0),
        "y": values.get("Y", 0),
        "width": values.get("WIDTH", 0),
        "height": values.get("HEIGHT", 0),
    }


def search_window_ids(display: str, *, only_visible: bool) -> list[str]:
    args = ["xdotool", "search"]
    if only_visible:
        args.append("--onlyvisible")
    args.extend(["--name", ""])
    result = run_command(args, env={"DISPLAY": display}, text=True, check=False)
    ids: list[str] = []
    for wid in result.stdout.splitlines():
        wid = wid.strip()
        if wid:
            ids.append(wid)
    return ids
