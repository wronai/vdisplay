"""GUI process discovery (ps /proc) for window correlation."""

from __future__ import annotations

import subprocess
from typing import Any

_GUI_COMM_HINTS = frozenset(
    {
        "pycharm",
        "idea",
        "webstorm",
        "goland",
        "clion",
        "rider",
        "codium",
        "code",
        "cursor",
        "windsurf",
        "firefox",
        "chrome",
        "chromium",
        "antigravity",
        "vscodium",
        "jetbrains-toolb",
        "jetbrainsd",
        "java",
    }
)

_GUI_CMDLINE_MARKERS = (
    "pycharm",
    "intellij",
    "jetbrains",
    "codium",
    "vscodium",
    "cursor",
    "windsurf",
    "antigravity",
    "firefox",
    "chrome",
    "code --",
    "Code -",
    "gnome-terminal",
    "konsole",
)


_SHELL_COMMS = frozenset(
    {
        "bash",
        "sh",
        "zsh",
        "dash",
        "grep",
        "sleep",
        "cat",
        "sed",
        "awk",
        "sort",
        "head",
        "tail",
        "tee",
        "xargs",
        "find",
        "python",
        "python3",
        "node",
        "npm",
        "curl",
        "wget",
    }
)


_ELECTRON_HELPER_TYPES = (
    "zygote",
    "gpu-process",
    "utility",
    "renderer",
    "broker",
    "extension",
    "sandbox-helper",
    "ppapi",
)


def _is_electron_helper(cmdline: str) -> bool:
    low = cmdline.lower()
    return any(f"--type={token}" in low for token in _ELECTRON_HELPER_TYPES)


def _is_browser_or_electron_helper(*, comm: str, cmdline: str) -> bool:
    comm_low = comm.lower()
    if comm_low in {
        "isolated",
        "privileged",
        "rdd",
        "socket",
        "utility",
        "web",
        "webextensions",
        "forkserver",
        "crashhelper",
        "chrome-sandbox",
        "chrome_crashpad",
        "language_server",
        "pyrefly",
        "embeddings-serv",
        "fsnotifier",
        "jetbrainsd",
        "koru",
        "vdisplay",
        "node",
        "npm",
        "mainthread",
    }:
        return True
    if comm_low in {"chrome", "cursor", "codium", "antigravity", "windsurf", "firefox"}:
        return _is_electron_helper(cmdline)
    return False


def _looks_like_gui_process(*, comm: str, cmdline: str) -> bool:
    comm_low = comm.lower()
    cmd_low = cmdline.lower()
    if _is_browser_or_electron_helper(comm=comm, cmdline=cmdline):
        return False
    if comm_low in _GUI_COMM_HINTS:
        return True
    if comm_low in _SHELL_COMMS:
        return False
    if comm_low == "java":
        return any(
            marker in cmd_low
            for marker in ("pycharm", "intellij", "jetbrains", "webstorm", "goland", "clion", "rider", "idea")
        )
    return any(marker in cmd_low for marker in _GUI_CMDLINE_MARKERS)


def list_gui_processes(*, limit: int = 128) -> dict[str, Any]:
    """Best-effort GUI-ish processes from ps (includes native Wayland apps)."""
    try:
        proc = subprocess.run(
            ["ps", "-eo", "pid,comm,args"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "error": str(exc), "processes": []}
    if proc.returncode != 0:
        return {"ok": False, "error": (proc.stderr or proc.stdout or "ps failed").strip(), "processes": []}

    found: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines()[1:]:
        parts = line.split(None, 2)
        if len(parts) < 2:
            continue
        try:
            pid = int(parts[0])
        except ValueError:
            continue
        comm = parts[1]
        cmdline = parts[2] if len(parts) > 2 else ""
        if not _looks_like_gui_process(comm=comm, cmdline=cmdline):
            continue
        found.append({"pid": pid, "comm": comm, "cmdline": cmdline})
        if len(found) >= limit:
            break
    return {"ok": True, "processes": found, "process_count": len(found)}


__all__ = ["_SHELL_COMMS", "_is_browser_or_electron_helper", "list_gui_processes"]
