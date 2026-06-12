"""Correlate X11, GNOME Shell, AT-SPI, and process metadata into unified surfaces."""

from __future__ import annotations

import os
import re
from typing import Any

from ..nl import assign_windows_to_monitors, find_monitor_for_window
from .constants import JUNK_CLASS_MARKERS
from .gnome_shell import list_gnome_meta_windows
from .processes import _SHELL_COMMS, _is_browser_or_electron_helper, list_gui_processes
from .query import list_windows_enriched


def _list_atspi_applications() -> dict[str, Any]:
    try:
        from ..control.providers.atspi import _run_subprocess
    except Exception as exc:
        return {"ok": False, "error": str(exc), "applications": []}
    try:
        result = _run_subprocess({"op": "list_applications"}, timeout_s=8.0)
    except Exception as exc:
        return {"ok": False, "error": str(exc), "applications": []}
    if not result.get("ok"):
        return {
            "ok": False,
            "error": str(result.get("error") or "atspi list_applications failed"),
            "applications": [],
        }
    apps = result.get("applications")
    if not isinstance(apps, list):
        return {"ok": False, "error": "atspi list_applications missing applications", "applications": []}
    return {"ok": True, "applications": apps, "application_count": len(apps)}


def _norm(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _tokens(text: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", _norm(text)) if len(t) >= 3}


def _title_similar(a: str | None, b: str | None) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    return inter / max(len(ta), len(tb))


def _classify_ide_hint(*parts: str | None) -> str | None:
    blob = " ".join(p for p in parts if p).lower()
    if any(x in blob for x in ("pycharm", "intellij", "jetbrains", "webstorm", "goland", "clion", "rider", "idea")):
        return "jetbrains"
    if any(x in blob for x in ("vscodium", "codium", "visual studio code", "vscode", " code ", "code-oss")):
        return "vscode"
    if "cursor" in blob:
        return "cursor"
    if "windsurf" in blob:
        return "windsurf"
    if "antigravity" in blob:
        return "antigravity"
    if "firefox" in blob:
        return "firefox"
    return None


def _classify_ide_hint_from_process(process: dict[str, Any] | None) -> str | None:
    if not process:
        return None
    comm = str(process.get("comm") or "").lower()
    cmdline = str(process.get("cmdline") or "")
    if comm in {"pycharm", "idea", "webstorm", "goland", "clion", "rider", "jetbrains-toolb", "jetbrainsd", "fsnotifier"}:
        return "jetbrains"
    if comm in {"codium", "vscodium", "code"}:
        return "vscode"
    if comm in {"mainthread", "embeddings-serv"}:
        return None
    if comm in {"cursor", "windsurf", "firefox", "chrome", "chromium"}:
        return comm if comm != "chromium" else "chrome"
    if comm == "java":
        return _classify_ide_hint(cmdline)
    if comm in _SHELL_COMMS:
        return None
    return _classify_ide_hint(comm, cmdline)


def _bounds_from_atspi(atspi: dict[str, Any] | None) -> dict[str, Any] | None:
    if not atspi:
        return None
    bounds = atspi.get("bounds")
    if isinstance(bounds, dict) and bounds.get("width") and bounds.get("height"):
        return bounds
    return None


def _monitor_for_bounds(bounds: dict[str, Any] | None, monitors: list[dict[str, Any]]) -> str | None:
    if not bounds or not monitors:
        return None
    monitor = find_monitor_for_window(bounds, monitors)
    if monitor:
        name = monitor.get("name") or monitor.get("label")
        return str(name) if name else None
    return None


def _surface_rank(row: dict[str, Any]) -> float:
    score = float(row.get("confidence") or 0)
    if row.get("monitor_name"):
        score += 0.35
    if row.get("bounds"):
        score += 0.15
    stack = str(row.get("stack") or "")
    if stack in {"x11", "xwayland", "wayland_native", "jetbrains_xwayland", "atspi_frame"}:
        score += 0.25
    name = str(row.get("display_name") or "").lower()
    if "toolbox" in name:
        score -= 0.5
    return score


def summarize_app_surfaces(surfaces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One best row per ide_hint (IDE / browser family), skipping helpers and Toolbox."""
    best_by_hint: dict[str, dict[str, Any]] = {}
    for row in surfaces:
        hint = row.get("ide_hint")
        if not hint:
            continue
        name = str(row.get("display_name") or "").lower()
        if hint == "jetbrains" and "toolbox" in name:
            continue
        proc = ((row.get("sources") or {}).get("process")) or {}
        if _is_browser_or_electron_helper(
            comm=str(proc.get("comm") or row.get("display_name") or ""),
            cmdline=str(proc.get("cmdline") or ""),
        ):
            continue
        rank = _surface_rank(row)
        prev = best_by_hint.get(str(hint))
        if prev is None or rank > _surface_rank(prev):
            best_by_hint[str(hint)] = row
    ranked = list(best_by_hint.values())
    ranked.sort(key=lambda row: (-_surface_rank(row), str(row.get("display_name") or "")))
    return ranked


def _monitor_name(monitors: list[dict[str, Any]], *, index: int | None) -> str | None:
    if index is None:
        return None
    for monitor in monitors:
        if monitor.get("monitor_index") == index or monitor.get("monitor_id") == index:
            name = monitor.get("name") or monitor.get("label")
            return str(name) if name else None
    return None


def _infer_stack(*, x11: dict[str, Any] | None, gnome: dict[str, Any] | None, atspi: dict[str, Any] | None = None) -> str:
    if x11 and gnome:
        return "xwayland"
    if x11:
        return "x11"
    if gnome:
        return "wayland_native"
    if atspi and _bounds_from_atspi(atspi):
        return "atspi_frame"
    return "process_only"


def _pick_display_name(
    *,
    gnome: dict[str, Any] | None,
    x11: dict[str, Any] | None,
    atspi: dict[str, Any] | None,
    process: dict[str, Any] | None,
) -> str:
    for candidate in (
        (gnome or {}).get("title"),
        (x11 or {}).get("title"),
        (x11 or {}).get("app_label"),
        (atspi or {}).get("window_title"),
        (atspi or {}).get("name"),
        (process or {}).get("comm"),
    ):
        text = str(candidate or "").strip()
        if text:
            return text
    return "unknown"


_JETBRAINS_IDE_COMMS = frozenset({"pycharm", "idea", "webstorm", "goland", "clion", "rider"})
_JETBRAINS_AWT_MARKERS = tuple(
    marker for marker in JUNK_CLASS_MARKERS if marker in {"kotlinx-coroutines", "sun-awt-x11-xcanvaspeer", "javaawtcanvas"}
)


def _is_jetbrains_awt_x11_window(win: dict[str, Any]) -> bool:
    blob = " ".join(
        str(win.get(key) or "") for key in ("wm_class", "wm_class_instance", "title", "name", "app_label")
    ).lower()
    return any(marker in blob for marker in _JETBRAINS_AWT_MARKERS)


def _is_jetbrains_ide_process(process: dict[str, Any] | None) -> bool:
    if not process:
        return False
    comm = str(process.get("comm") or "").lower()
    if comm in _JETBRAINS_IDE_COMMS:
        return True
    if comm == "java":
        cmdline = str(process.get("cmdline") or "").lower()
        return any(name in cmdline for name in _JETBRAINS_IDE_COMMS)
    return False


def _bounds_union(windows: list[dict[str, Any]]) -> dict[str, int] | None:
    coords: list[tuple[int, int, int, int]] = []
    for win in windows:
        x, y = win.get("x"), win.get("y")
        width, height = win.get("width"), win.get("height")
        if not all(isinstance(value, int) for value in (x, y, width, height)):
            continue
        if width <= 0 or height <= 0:
            continue
        coords.append((x, y, x + width, y + height))
    if not coords:
        return None
    x1 = min(item[0] for item in coords)
    y1 = min(item[1] for item in coords)
    x2 = max(item[2] for item in coords)
    y2 = max(item[3] for item in coords)
    return {"x": x1, "y": y1, "width": x2 - x1, "height": y2 - y1}


def _display_name_for_jetbrains_process(process: dict[str, Any]) -> str:
    comm = str(process.get("comm") or "").lower()
    if comm == "pycharm":
        return "PyCharm"
    if comm in _JETBRAINS_IDE_COMMS:
        return comm.replace("_", " ").title()
    cmdline = str(process.get("cmdline") or "").lower()
    for name, label in (
        ("pycharm", "PyCharm"),
        ("webstorm", "WebStorm"),
        ("goland", "GoLand"),
        ("clion", "CLion"),
        ("rider", "Rider"),
        ("idea", "IntelliJ IDEA"),
    ):
        if name in cmdline:
            return label
    return "JetBrains IDE"


def apply_jetbrains_wayland_heuristic(
    surfaces: list[dict[str, Any]],
    *,
    awt_proxies: list[dict[str, Any]],
    monitors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Link native Wayland JetBrains IDE processes to Java AWT/XWayland proxy windows."""
    if not awt_proxies:
        return surfaces

    proxies_by_monitor: dict[str, list[dict[str, Any]]] = {}
    for win in awt_proxies:
        bounds = {
            "x": win.get("x"),
            "y": win.get("y"),
            "width": win.get("width"),
            "height": win.get("height"),
        }
        monitor_name = win.get("monitor_name") or _monitor_for_bounds(bounds, monitors)
        if not monitor_name:
            continue
        proxies_by_monitor.setdefault(str(monitor_name), []).append(win)
    if not proxies_by_monitor:
        return surfaces

    def _monitor_proxy_score(monitor: str) -> tuple[int, int]:
        proxies = proxies_by_monitor[monitor]
        union = _bounds_union(proxies) or {}
        area = int(union.get("width") or 0) * int(union.get("height") or 0)
        return len(proxies), area

    best_monitor = max(proxies_by_monitor.keys(), key=_monitor_proxy_score)
    proxies = proxies_by_monitor[best_monitor]
    bounds = _bounds_union(proxies)

    for row in surfaces:
        proc = ((row.get("sources") or {}).get("process")) or {}
        if row.get("ide_hint") != "jetbrains" or not _is_jetbrains_ide_process(proc):
            continue
        if row.get("monitor_name") and str(row.get("stack") or "") not in {"process_only"}:
            continue
        row["display_name"] = _display_name_for_jetbrains_process(proc)
        row["monitor_name"] = best_monitor
        row["bounds"] = bounds
        row["stack"] = "jetbrains_xwayland"
        row["confidence"] = round(max(float(row.get("confidence") or 0), 0.68), 3)
        reasons = list(row.get("match_reasons") or [])
        if "jetbrains_awt_x11_proxy" not in reasons:
            reasons.append("jetbrains_awt_x11_proxy")
        row["match_reasons"] = reasons
        sources = dict(row.get("sources") or {})
        sources["x11_awt_proxies"] = proxies
        row["sources"] = sources
    return surfaces


def correlate_surfaces(
    *,
    x11_windows: list[dict[str, Any]],
    gnome_windows: list[dict[str, Any]],
    atspi_apps: list[dict[str, Any]],
    processes: list[dict[str, Any]],
    monitors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge discovery sources into one row per logical app/window."""
    proc_by_pid = {int(p["pid"]): p for p in processes if isinstance(p.get("pid"), int)}
    x11_by_pid: dict[int, list[dict[str, Any]]] = {}
    for win in x11_windows:
        pid = win.get("pid")
        if isinstance(pid, int):
            x11_by_pid.setdefault(pid, []).append(win)

    gnome_by_pid: dict[int, list[dict[str, Any]]] = {}
    orphan_gnome: list[dict[str, Any]] = []
    for row in gnome_windows:
        pid = row.get("pid")
        if isinstance(pid, int) and pid > 0:
            gnome_by_pid.setdefault(pid, []).append(row)
        else:
            orphan_gnome.append(row)

    atspi_by_pid = {int(a["pid"]): a for a in atspi_apps if isinstance(a.get("pid"), int)}
    used_gnome: set[int] = set()
    used_x11: set[str] = set()
    used_atspi: set[int | str] = set()
    used_proc: set[int] = set()
    surfaces: list[dict[str, Any]] = []

    def _append_surface(
        *,
        pid: int | None,
        gnome: dict[str, Any] | None,
        x11: dict[str, Any] | None,
        atspi: dict[str, Any] | None,
        process: dict[str, Any] | None,
        confidence: float,
        match_reasons: list[str],
    ) -> None:
        title = _pick_display_name(gnome=gnome, x11=x11, atspi=atspi, process=process)
        monitor_name = None
        bounds = None
        if gnome:
            monitor_name = _monitor_name(monitors, index=gnome.get("monitor_index"))
            bounds = {
                "x": gnome.get("x"),
                "y": gnome.get("y"),
                "width": gnome.get("width"),
                "height": gnome.get("height"),
            }
        elif x11:
            monitor_name = x11.get("monitor_name")
            bounds = {
                "x": x11.get("x"),
                "y": x11.get("y"),
                "width": x11.get("width"),
                "height": x11.get("height"),
            }
        else:
            atspi_bounds = _bounds_from_atspi(atspi)
            if atspi_bounds:
                bounds = atspi_bounds
                monitor_name = _monitor_for_bounds(atspi_bounds, monitors)
        ide_hint = _classify_ide_hint(
            title,
            (gnome or {}).get("wm_class"),
            (x11 or {}).get("wm_class"),
            (x11 or {}).get("process_name"),
            (atspi or {}).get("name"),
            (atspi or {}).get("window_title"),
        )
        if ide_hint is None and process is not None and not (x11 or gnome or atspi):
            ide_hint = _classify_ide_hint_from_process(process)
        elif ide_hint is None and process is not None:
            ide_hint = _classify_ide_hint_from_process(process)
        surface_id = f"surface:{pid or 'na'}:{_norm(title)[:48] or 'unknown'}"
        surfaces.append(
            {
                "id": surface_id,
                "display_name": title,
                "pid": pid,
                "ide_hint": ide_hint,
                "stack": _infer_stack(x11=x11, gnome=gnome, atspi=atspi),
                "monitor_name": monitor_name,
                "bounds": bounds,
                "confidence": round(min(1.0, max(0.0, confidence)), 3),
                "match_reasons": match_reasons,
                "sources": {
                    "gnome_shell": gnome,
                    "x11": x11,
                    "atspi": atspi,
                    "process": process,
                },
            }
        )

    all_pids = sorted(
        {
            pid
            for pid in (
                set(proc_by_pid)
                | set(x11_by_pid)
                | set(gnome_by_pid)
                | set(atspi_by_pid)
            )
            if pid > 0
        }
    )
    for pid in all_pids:
        gnome_rows = gnome_by_pid.get(pid) or []
        gnome = gnome_rows[0] if gnome_rows else None
        if gnome_rows:
            used_gnome.add(id(gnome_rows[0]))
        x11_rows = x11_by_pid.get(pid) or []
        x11 = x11_rows[0] if x11_rows else None
        if x11 is not None:
            used_x11.add(str(x11.get("window_id")))
        atspi = atspi_by_pid.get(pid)
        if atspi is not None:
            used_atspi.add(pid)
        process = proc_by_pid.get(pid)
        if process is not None:
            used_proc.add(pid)
        reasons: list[str] = []
        score = 0.35
        if process:
            reasons.append("process_pid")
            score += 0.15
        if gnome:
            reasons.append("gnome_shell_pid")
            score += 0.25
        if x11:
            reasons.append("x11_pid")
            score += 0.2
        if atspi:
            reasons.append("atspi_pid")
            score += 0.15
        if gnome and x11:
            reasons.append("gnome_x11_same_pid")
            score += 0.1
        _append_surface(
            pid=pid,
            gnome=gnome,
            x11=x11,
            atspi=atspi,
            process=process,
            confidence=score,
            match_reasons=reasons,
        )

    for gnome in gnome_windows:
        if id(gnome) in used_gnome:
            continue
        matched_x11 = None
        best = 0.0
        for win in x11_windows:
            wid = str(win.get("window_id"))
            if wid in used_x11:
                continue
            sim = max(
                _title_similar(gnome.get("title"), win.get("title")),
                _title_similar(gnome.get("title"), win.get("app_label")),
                _title_similar(gnome.get("wm_class"), win.get("wm_class")),
            )
            if sim > best:
                best = sim
                matched_x11 = win
        proc = None
        pid = gnome.get("pid")
        if isinstance(pid, int) and pid in proc_by_pid:
            proc = proc_by_pid[pid]
        atspi = None
        for app in atspi_apps:
            if app.get("pid") in (None, pid):
                continue
            sim = max(
                _title_similar(gnome.get("title"), app.get("window_title")),
                _title_similar(gnome.get("title"), app.get("name")),
            )
            if sim >= 0.34:
                atspi = app
                break
        reasons = ["gnome_shell_orphan"]
        score = 0.45
        if matched_x11 and best >= 0.34:
            reasons.append(f"title_match:{best:.2f}")
            score += 0.25
            used_x11.add(str(matched_x11.get("window_id")))
        if proc:
            reasons.append("process_name_match")
            score += 0.1
        _append_surface(
            pid=pid if isinstance(pid, int) else None,
            gnome=gnome,
            x11=matched_x11,
            atspi=atspi,
            process=proc,
            confidence=score,
            match_reasons=reasons,
        )

    for win in x11_windows:
        wid = str(win.get("window_id"))
        if wid in used_x11:
            continue
        pid = win.get("pid") if isinstance(win.get("pid"), int) else None
        proc = proc_by_pid.get(pid) if pid else None
        _append_surface(
            pid=pid,
            gnome=None,
            x11=win,
            atspi=None,
            process=proc,
            confidence=0.4,
            match_reasons=["x11_unmatched"],
        )

    def _atspi_key(app: dict[str, Any]) -> int | str:
        app_index = app.get("app_index")
        if isinstance(app_index, int):
            return f"atspi:{app_index}"
        return f"atspi:{id(app)}"

    for app in atspi_apps:
        akey = _atspi_key(app)
        if akey in used_atspi:
            continue
        pid = app.get("pid")
        if isinstance(pid, int) and pid in used_atspi:
            continue
        matched_proc = proc_by_pid.get(pid) if isinstance(pid, int) else None
        matched_x11 = None
        matched_gnome = None
        title = str(app.get("window_title") or app.get("name") or "")
        if title:
            for win in x11_windows:
                wid = str(win.get("window_id"))
                if wid in used_x11:
                    x11_pid = win.get("pid")
                    if isinstance(x11_pid, int) and x11_pid in used_proc:
                        sim = max(
                            _title_similar(title, win.get("title")),
                            _title_similar(title, win.get("app_label")),
                        )
                        if sim >= 0.5:
                            used_atspi.add(akey)
                            matched_x11 = None
                            break
                    continue
                sim = max(
                    _title_similar(title, win.get("title")),
                    _title_similar(title, win.get("app_label")),
                )
                if sim >= 0.5:
                    matched_x11 = win
                    used_x11.add(wid)
                    break
            if matched_x11 is None and not (akey in used_atspi):
                for gnome in gnome_windows:
                    if id(gnome) in used_gnome:
                        continue
                    sim = _title_similar(title, gnome.get("title"))
                    if sim >= 0.5:
                        matched_gnome = gnome
                        used_gnome.add(id(gnome))
                        if isinstance(gnome.get("pid"), int):
                            matched_proc = proc_by_pid.get(int(gnome["pid"]))
                        break
            if matched_proc is None and title and not (akey in used_atspi):
                for candidate in processes:
                    cpid = candidate.get("pid")
                    if not isinstance(cpid, int) or cpid in used_proc:
                        continue
                    sim = max(
                        _title_similar(title, candidate.get("comm")),
                        _title_similar(title, candidate.get("cmdline")),
                    )
                    if sim >= 0.34:
                        matched_proc = candidate
                        used_proc.add(cpid)
                        pid = cpid
                        break
        if akey in used_atspi:
            continue
        if isinstance(pid, int):
            used_atspi.add(pid)
        used_atspi.add(akey)
        if matched_proc is not None and isinstance(matched_proc.get("pid"), int):
            used_proc.add(int(matched_proc["pid"]))
        if matched_x11 is not None and isinstance(matched_x11.get("pid"), int):
            if int(matched_x11["pid"]) in used_proc:
                continue
        _append_surface(
            pid=pid if isinstance(pid, int) else (matched_proc or {}).get("pid"),
            gnome=matched_gnome,
            x11=matched_x11,
            atspi=app,
            process=matched_proc,
            confidence=0.62 if matched_x11 or matched_gnome or matched_proc else 0.48,
            match_reasons=["atspi_title_match" if title else "atspi_unmatched"],
        )

    for pid, proc in proc_by_pid.items():
        if pid in used_proc:
            continue
        if _is_browser_or_electron_helper(
            comm=str(proc.get("comm") or ""),
            cmdline=str(proc.get("cmdline") or ""),
        ):
            continue
        _append_surface(
            pid=pid,
            gnome=None,
            x11=None,
            atspi=atspi_by_pid.get(pid),
            process=proc,
            confidence=0.3,
            match_reasons=["process_only"],
        )

    surfaces.sort(
        key=lambda row: (
            -(row.get("confidence") or 0),
            row.get("monitor_name") or "",
            row.get("display_name") or "",
        )
    )
    return surfaces


def build_surface_registry(
    display: str,
    *,
    monitors: list[dict[str, Any]] | None = None,
    apps_only: bool = True,
) -> dict[str, Any]:
    """Collect X11 + GNOME + AT-SPI + ps and return correlated surfaces."""
    from ..discovery import list_outputs

    if monitors is None:
        try:
            monitors = list_outputs(display, enrich_nl=False)
        except Exception:
            monitors = []

    x11_windows = list_windows_enriched(display, only_visible=True, apps_only=apps_only)
    x11_windows = assign_windows_to_monitors(x11_windows, monitors)
    x11_all = list_windows_enriched(display, only_visible=True, apps_only=False)
    x11_all = assign_windows_to_monitors(x11_all, monitors)
    awt_proxies = [win for win in x11_all if _is_jetbrains_awt_x11_window(win)]
    gnome_payload = list_gnome_meta_windows()
    atspi_payload = _list_atspi_applications()
    process_payload = list_gui_processes()

    surfaces = correlate_surfaces(
        x11_windows=x11_windows,
        gnome_windows=list(gnome_payload.get("windows") or []),
        atspi_apps=list(atspi_payload.get("applications") or []),
        processes=list(process_payload.get("processes") or []),
        monitors=monitors,
    )
    surfaces = apply_jetbrains_wayland_heuristic(
        surfaces,
        awt_proxies=awt_proxies,
        monitors=monitors,
    )
    app_surfaces = summarize_app_surfaces(surfaces)

    session_type = os.environ.get("XDG_SESSION_TYPE", "unknown")
    return {
        "session_type": session_type,
        "x11_window_count": len(x11_windows),
        "gnome_window_count": gnome_payload.get("window_count", 0),
        "atspi_application_count": atspi_payload.get("application_count", 0),
        "process_count": process_payload.get("process_count", 0),
        "jetbrains_awt_proxy_count": len(awt_proxies),
        "surface_count": len(surfaces),
        "sources": {
            "x11": {"window_source": "x11", "hint": "xdotool / XWayland clients only"},
            "gnome_shell": {
                "ok": gnome_payload.get("ok"),
                "error": gnome_payload.get("error"),
                "hint": "Mutter meta windows (native Wayland + XWayland)",
            },
            "atspi": {
                "ok": atspi_payload.get("ok"),
                "error": atspi_payload.get("error"),
                "hint": "AT-SPI2 application roots (name, pid, frame title)",
            },
            "processes": {
                "ok": process_payload.get("ok"),
                "error": process_payload.get("error"),
                "hint": "ps scan for GUI-like processes (includes headless/helpers)",
            },
        },
        "gnome_windows": gnome_payload.get("windows") or [],
        "atspi_applications": atspi_payload.get("applications") or [],
        "processes": process_payload.get("processes") or [],
        "surfaces": surfaces,
        "app_surfaces": app_surfaces,
        "app_surface_count": len(app_surfaces),
    }


__all__ = [
    "apply_jetbrains_wayland_heuristic",
    "build_surface_registry",
    "correlate_surfaces",
    "summarize_app_surfaces",
]
