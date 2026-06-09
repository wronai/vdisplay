from __future__ import annotations

import re
from pathlib import Path

from .constants import FRAME_CLASSES, JUNK_TITLES
from .filter import looks_like_internal_class, looks_like_internal_name


def parse_wm_class(raw: str) -> tuple[str, str]:
    if not raw:
        return "", ""
    parts = re.findall(r'"([^"]*)"', raw)
    if not parts and "," in raw:
        parts = [p.strip() for p in raw.split(",", 1)]
    if len(parts) >= 2:
        return parts[0].strip(), parts[1].strip()
    if len(parts) == 1:
        return parts[0], parts[0]
    return raw.strip(), raw.strip()


def normalize_atom_list(raw: str) -> str:
    if not raw:
        return ""
    atoms = re.findall(r"_NET_WM_WINDOW_TYPE_(\w+)", raw.upper())
    if atoms:
        return atoms[-1].lower()
    return raw.strip("() ").split("/")[-1].lower()


def resolve_window_pid(display: str, window_id: str, props: dict[str, str]) -> int | None:
    from .scan import xdotool

    pid_raw = props.get("_NET_WM_PID", "").strip()
    if pid_raw.isdigit():
        return int(pid_raw)
    out = xdotool(display, "getwindowpid", window_id).strip()
    if out.isdigit():
        return int(out)
    return None


def process_info(pid: int | None) -> dict[str, str | None]:
    if pid is None or pid <= 0:
        return {"name": None, "cmdline": None}
    comm = Path(f"/proc/{pid}/comm")
    cmdline = Path(f"/proc/{pid}/cmdline")
    name = comm.read_text(encoding="utf-8").strip() if comm.exists() else None
    cmd = None
    if cmdline.exists():
        raw = cmdline.read_bytes().replace(b"\x00", b" ").strip()
        cmd = raw.decode("utf-8", errors="replace")[:240] or None
    return {"name": name, "cmdline": cmd}


def usable_title(candidate: str) -> bool:
    return bool(candidate) and candidate.lower() not in JUNK_TITLES and not looks_like_internal_name(candidate)


def derive_app_label(
    *,
    title: str,
    net_wm_name: str,
    wm_name: str,
    wm_instance: str,
    wm_class: str,
    process_name: str | None,
) -> str:
    for candidate in (title, net_wm_name, wm_name):
        if usable_title(candidate):
            return candidate.strip()
    if process_name and process_name not in {"mutter-x11-frames", "xdg-desktop-portal-gnome"}:
        return process_name
    if wm_instance and not looks_like_internal_class(wm_instance):
        return wm_instance
    if wm_class and wm_class not in FRAME_CLASSES and not looks_like_internal_class(wm_class):
        return wm_class
    return title or net_wm_name or wm_name or wm_class or "(unknown)"


def derive_role(
    *,
    window_id: str,
    root_id: str,
    wm_class: str,
    width: int,
    height: int,
    title: str,
    net_wm_name: str,
) -> str:
    if window_id == root_id:
        return "root"
    if wm_class in FRAME_CLASSES or "mutter-x11-frames" in wm_class:
        return "frame"
    if width <= 1 or height <= 1:
        return "helper"
    lowered = f"{title} {net_wm_name}".lower()
    if "guard" in lowered:
        return "helper"
    if looks_like_internal_class(wm_class) or looks_like_internal_name(net_wm_name or title):
        return "client"
    return "application"
