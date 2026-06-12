"""GNOME Shell meta-window discovery via org.gnome.Shell.Eval."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from typing import Any

from ..hmi.pointer_probes import session_env

_GNOME_LIST_WINDOWS_SCRIPT = """
JSON.stringify(
  global.get_window_actors().map(function (a) {
    var w = a.metaWindow;
    if (!w) return null;
    var r = w.get_frame_rect();
    return {
      title: w.get_title() || "",
      wm_class: w.get_wm_class() || "",
      pid: w.get_pid(),
      minimized: !!w.minimized,
      maximized: !!w.maximized,
      monitor_index: w.get_monitor().index(),
      x: r.x,
      y: r.y,
      width: r.width,
      height: r.height,
    };
  }).filter(function (x) {
    return x && (x.title || x.wm_class);
  })
)
"""


def _parse_gnome_eval_stdout(text: str) -> tuple[bool, str]:
    match = re.search(r"\(\s*(true|false)\s*,\s*'((?:\\'|[^'])*)'\s*\)", text, flags=re.IGNORECASE)
    if not match:
        return False, text.strip()
    ok = match.group(1).lower() == "true"
    payload = match.group(2).replace("\\'", "'")
    return ok, payload


def list_gnome_meta_windows(*, timeout_s: float = 3.0) -> dict[str, Any]:
    """Return compositor-level windows (includes native Wayland clients)."""
    if shutil.which("gdbus") is None:
        return {"ok": False, "error": "gdbus not on PATH", "windows": []}
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
                _GNOME_LIST_WINDOWS_SCRIPT.strip(),
            ],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
            env=session_env(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "error": str(exc), "windows": []}
    text = (proc.stdout or proc.stderr or "").strip()
    if proc.returncode != 0:
        return {"ok": False, "error": text or "gdbus Eval failed", "windows": []}
    eval_ok, payload = _parse_gnome_eval_stdout(text)
    if not eval_ok:
        return {"ok": False, "error": payload or "gnome Eval returned false", "windows": []}
    try:
        rows = json.loads(payload)
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"gnome Eval JSON parse failed: {exc}; payload={payload[:200]!r}", "windows": []}
    if not isinstance(rows, list):
        return {"ok": False, "error": "gnome Eval payload is not a list", "windows": []}
    windows: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        windows.append(
            {
                "source": "gnome_shell",
                "title": str(row.get("title") or ""),
                "wm_class": str(row.get("wm_class") or ""),
                "pid": int(row["pid"]) if row.get("pid") not in (None, "") else None,
                "minimized": bool(row.get("minimized")),
                "maximized": bool(row.get("maximized")),
                "monitor_index": row.get("monitor_index"),
                "x": int(row.get("x") or 0),
                "y": int(row.get("y") or 0),
                "width": int(row.get("width") or 0),
                "height": int(row.get("height") or 0),
            }
        )
    return {"ok": True, "windows": windows, "window_count": len(windows)}


__all__ = ["list_gnome_meta_windows"]
