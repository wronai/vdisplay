"""Live-system adapters for the deterministic capture-coordinate contract."""

from __future__ import annotations

from typing import Any

from .coordinate_contract import canonicalize_capture_meta


def resolve_live_capture_meta(
    source: str,
    *,
    display: str | None = None,
    default_size: tuple[int, int] = (2048, 1280),
) -> dict[str, Any]:
    """Resolve a current monitor/ScreenCast snapshot into canonical metadata."""
    from ..application.services.discovery import list_monitors_local

    monitors = list(list_monitors_local(display=display).get("monitors") or [])
    monitor = next(
        (row for row in monitors if str(row.get("name") or "") == source),
        None,
    )
    meta: dict[str, Any] = {"source": source, "monitor_name": source}
    if isinstance(monitor, dict):
        meta["rotation"] = monitor.get("rotation") or "normal"

    try:
        from .portal_screencast import get_active_screencast
        from .screencast_crop import resolve_multi_stream_region
        from .screencast_stream_matching import screencast_stream_index_for_monitor

        session = get_active_screencast()
        if session is not None and isinstance(monitor, dict):
            stream_index = screencast_stream_index_for_monitor(
                session,
                monitor,
                all_monitors=monitors or [monitor],
            )
            region = resolve_multi_stream_region(session, stream_index, monitor)
            if isinstance(region, dict):
                meta.update(
                    {
                        "region": dict(region),
                        "screencast_stream": True,
                        "screencast_stream_index": stream_index,
                        "width": int(region.get("width") or 0),
                        "height": int(region.get("height") or 0),
                    }
                )
    except Exception:
        pass

    if "region" not in meta:
        meta["width"], meta["height"] = default_size
    return canonicalize_capture_meta(
        meta,
        source=source,
        monitor=monitor,
        default_size=default_size,
    )


__all__ = ["resolve_live_capture_meta"]
