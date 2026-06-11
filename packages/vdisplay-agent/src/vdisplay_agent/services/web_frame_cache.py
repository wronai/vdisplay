"""TTL cache and capture helpers for the web console monitor frames."""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path
from typing import Any

from vdisplay.capture.host import capture_all_monitors, capture_host_to_file
from vdisplay.exceptions import VDisplayError

from ..runtime import AgentRuntime

_FRAME_CACHE: dict[str, tuple[float, Path, dict[str, Any]]] = {}
_FRAME_CACHE_TTL_S = max(
    0.5,
    float(os.environ.get("VDISPLAY_WEB_FRAME_CACHE_TTL_S", "5.0")),
)


def _require_screencast(runtime: AgentRuntime) -> None:
    session = runtime.store.screencast
    if session is not None and session.is_ready:
        return
    raise VDisplayError(
        "screencast not ready — run once from a GUI terminal: vdisplay agent screencast start "
        "(choose All Screens in the GNOME portal). Automatic portal prompts are disabled "
        "to avoid repeated permission dialogs."
    )


def cache_get(key: str) -> tuple[Path, dict[str, Any]] | None:
    hit = _FRAME_CACHE.get(key)
    if hit is None:
        return None
    ts, path, meta = hit
    if time.monotonic() - ts > _FRAME_CACHE_TTL_S:
        return None
    if path.is_file():
        return path, meta
    return None


def cache_put(key: str, path: Path, meta: dict[str, Any]) -> None:
    _FRAME_CACHE[key] = (time.monotonic(), path, meta)


def capture_monitor_frame_with_meta(
    runtime: AgentRuntime,
    monitor_name: str,
    *,
    display: str | None = None,
    use_cache: bool = True,
) -> tuple[Path, dict[str, Any]]:
    cache_key = f"{display or ':0'}:{monitor_name}"
    if use_cache:
        cached = cache_get(cache_key)
        if cached is not None:
            return cached

    _require_screencast(runtime)

    with tempfile.TemporaryDirectory(prefix="vdisplay-web-") as tmpdir:
        out = Path(tmpdir) / f"{monitor_name}.png"
        try:
            meta = capture_host_to_file(
                out,
                display=display,
                source=monitor_name,
                screencast_session=runtime.store.screencast,
            )
        except VDisplayError:
            if runtime.store.screencast is not None and not runtime.store.screencast.is_ready:
                runtime.store.screencast = None
            raise
        src = Path(str(meta.get("path") or out))
        if not src.is_file():
            raise VDisplayError(f"capture failed for monitor {monitor_name}")
        persistent = Path(tempfile.gettempdir()) / "vdisplay-web-cache" / f"{cache_key.replace(':', '_')}.png"
        persistent.parent.mkdir(parents=True, exist_ok=True)
        persistent.write_bytes(src.read_bytes())
        capture_meta = dict(meta)
        cache_put(cache_key, persistent, capture_meta)
        return persistent, capture_meta


def capture_monitor_frame(
    runtime: AgentRuntime,
    monitor_name: str,
    *,
    display: str | None = None,
    use_cache: bool = True,
) -> Path:
    path, _meta = capture_monitor_frame_with_meta(
        runtime,
        monitor_name,
        display=display,
        use_cache=use_cache,
    )
    return path


def _get_cached_all_frames(cache_key: str) -> list[dict[str, Any]] | None:
    cached = cache_get(cache_key)
    if cached is not None and cached[0].parent.is_dir():
        return [
            {
                "monitor_name": path.stem.replace("latest-", ""),
                "path": str(path),
            }
            for path in sorted(cached[0].parent.glob("latest-*.png"))
        ]
    return None


def _capture_bulk_or_fallback(runtime: AgentRuntime, display: str | None, tmpdir: str) -> list[dict[str, Any]]:
    _require_screencast(runtime)
    try:
        bulk = capture_all_monitors(
            display=display,
            out_dir=tmpdir,
            screencast_session=runtime.store.screencast,
        )
        captures = list(bulk.get("captures") or [])
        if captures:
            return captures
    except VDisplayError:
        pass

    outputs = runtime.outputs(display=display, include_all=True)
    monitors = list(outputs.get("monitors") or [])
    frames: list[dict[str, Any]] = []
    for item in monitors:
        name = str(item.get("name") or item.get("label") or "")
        if not name:
            continue
        path = capture_monitor_frame(runtime, name, display=display, use_cache=False)
        frames.append({"monitor_name": name, "path": str(path), "meta": item})
    return frames


def _persist_captures_to_cache(cache_key: str, captures: list[dict[str, Any]]) -> None:
    if not captures:
        return
    cache_dir = Path(tempfile.gettempdir()) / "vdisplay-web-cache" / cache_key.replace(":", "_")
    cache_dir.mkdir(parents=True, exist_ok=True)
    frames: list[dict[str, Any]] = []
    for cap in captures:
        name = str(cap.get("monitor_name") or cap.get("source") or "monitor")
        src = Path(str(cap.get("path") or ""))
        if not src.is_file():
            continue
        dest = cache_dir / f"latest-{name}.png"
        dest.write_bytes(src.read_bytes())
        frames.append({"monitor_name": name, "path": str(dest), "meta": cap})
    if frames:
        cache_put(cache_key, cache_dir / f"latest-{frames[0]['monitor_name']}.png", dict(frames[0].get("meta") or {}))


def capture_all_monitor_frames(
    runtime: AgentRuntime,
    *,
    display: str | None = None,
    use_cache: bool = True,
) -> list[dict[str, Any]]:
    cache_key = f"{display or ':0'}:__all__"
    if use_cache:
        cached = _get_cached_all_frames(cache_key)
        if cached is not None:
            return cached

    with tempfile.TemporaryDirectory(prefix="vdisplay-web-all-") as tmpdir:
        captures = _capture_bulk_or_fallback(runtime, display, tmpdir)

    _persist_captures_to_cache(cache_key, captures)
    return captures
