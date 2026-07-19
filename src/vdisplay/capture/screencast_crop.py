"""Portal ScreenCast capture and monitor crop helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..exceptions import VDisplayError
from .linux_xwd import _crop_png, _is_wayland_session, is_blank_png
from .observation import png_dimensions
from .portal_screencast import (
    get_active_screencast,
    invalidate_screencast_session,
    screencast_stream_region,
    screencast_stream_region_for_index,
    screencast_stream_region_for_monitor,
)
from .screencast_keeper import keeper_manages_session, request_keeper_capture
from .screencast_stream_matching import (
    screencast_stream_index_for_monitor,
    screencast_stream_map,
    session_has_multiple_streams,
)

def build_screencast_crop_meta(
    session: Any,
    png: bytes,
    *,
    monitor: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if monitor is not None:
        stream_region = screencast_stream_region_for_monitor(session, monitor)
    else:
        stream_region = screencast_stream_region(session)
    png_w, png_h = png_dimensions(png)
    crop_meta: dict[str, Any] = {
        "screencast_full_frame": True,
        "screencast_stream": bool(stream_region),
    }
    if stream_region is not None:
        crop_meta["region"] = stream_region
    if png_w > 0 and png_h > 0:
        crop_meta["width"] = png_w
        crop_meta["height"] = png_h
    return crop_meta


def crop_global_region_from_screencast(
    png: bytes,
    region: tuple[int, int, int, int],
    crop_meta: dict[str, Any],
    *,
    display: str | None = None,
) -> tuple[bytes, tuple[int, int, int, int] | None]:
    from ..input.coords import global_region_to_capture_local

    local_region = global_region_to_capture_local(region, crop_meta, display=display)
    target_region = local_region if local_region is not None else region
    cropped = _crop_png(png, target_region)
    if is_blank_png(cropped):
        return png, None
    return cropped, local_region


def _resolve_active_session(screencast_session: Any, errors: list[str]) -> Any | None:
    session = screencast_session or get_active_screencast()
    if session is None or not session.is_ready:
        hint = "vdisplay agent screencast start"
        if _is_wayland_session():
            hint = (
                "vdisplay-agent serve, then vdisplay agent screencast start "
                "(or export VDISPLAY_AGENT_URL=http://127.0.0.1:8765)"
            )
        errors.append(f"portal-screencast: no active session (run: {hint})")
        return None
    return session


def _capture_screencast_png_via_keeper_or_direct(
    session: Any, node_index: int, errors: list[str], timeout_s: float = 30.0
) -> bytes | None:
    """Capture frame preferring keeper delegation (when the interactive keeper owns the
    portal session and its fd) to avoid the agent calling OpenPipeWireRemote itself
    (which can fail with "Invalid session" / AccessDenied if the keeper is the creator).
    Falls back to direct session.capture_png if no keeper is managing it.
    """
    spath = getattr(session, "session_path", None) or ""
    if keeper_manages_session(spath):
        for cand in (node_index, 0):
            try:
                return request_keeper_capture(
                    node_index=cand, session_path=spath or None, timeout_s=timeout_s
                )
            except (VDisplayError, TimeoutError) as exc:
                err_lower = str(exc).lower()
                errors.append(f"keeper capture failed (node_index={cand}): {exc}")
                if "invalid session" in err_lower or "access denied" in err_lower:
                    try:
                        from .screencast_keeper import stop_keeper
                        stop_keeper()
                    except Exception:
                        pass
                if cand == 0:
                    break
                # otherwise try the full "All Screens" stream (index 0) + let crop handle the monitor rect
                continue
        # Do NOT auto-stop on plain "timed out" — the stream for this particular
        # source may simply be slow or need the full-frame (index 0) + crop path.
        # When keeper-managed, direct capture via capture_png will also try the
        # keeper (session_uses_keeper), so skip the redundant fallback.
        if keeper_manages_session(spath):
            return None
    try:
        return session.capture_png(node_index=node_index)
    except VDisplayError as exc:
        errors.append(str(exc))
        return None


def _capture_screencast_png(session: Any, stream_idx: int, errors: list[str]) -> bytes | None:
    png = _capture_screencast_png_via_keeper_or_direct(session, stream_idx, errors)
    if png is None:
        # the helper already appended to errors; also do the target-not-found invalidation
        # if the last error was that (the direct or keeper may have reported it)
        last_err = errors[-1] if errors else ""
        if "target not found" in last_err.lower():
            invalidate_screencast_session(session)
            errors.append(
                " (stale screencast session auto-invalidated — run `vdisplay agent screencast start` to refresh)"
            )
    return png


def _maybe_crop_screencast_png(
    session: Any,
    png: bytes,
    region: tuple[int, int, int, int] | None,
    multi_stream: bool,
    monitor: dict[str, Any] | None,
    display: str | None,
) -> tuple[bytes, tuple[int, int, int, int] | None, dict[str, int] | None]:
    crop_region = region
    region_local: dict[str, int] | None = None
    if crop_region is not None and not multi_stream:
        crop_meta = build_screencast_crop_meta(session, png, monitor=monitor)
        cropped, local_region = crop_global_region_from_screencast(
            png, crop_region, crop_meta, display=display
        )
        if local_region is not None:
            png = cropped
            region_local = {
                "x": local_region[0],
                "y": local_region[1],
                "width": local_region[2],
                "height": local_region[3],
            }
        else:
            crop_region = None
    elif multi_stream:
        crop_region = None
    return png, crop_region, region_local


def resolve_multi_stream_region(
    session: Any,
    stream_idx: int,
    monitor: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Return the best canonical region for a stream in a multi-stream session."""
    if monitor is not None:
        region = screencast_stream_region_for_index(session, stream_idx)
        if region is None:
            region = screencast_stream_region_for_monitor(session, monitor)
        if region is not None:
            return region
    if stream_idx is None:
        return None
    streams = list(getattr(session, "streams", None) or [])
    if not (0 <= stream_idx < len(streams)):
        return None
    props = streams[stream_idx].get("properties") or {}
    pos = props.get("position") or [0, 0]
    sz = props.get("size") or [0, 0]
    if len(pos) >= 2 and len(sz) >= 2 and int(sz[0]) > 0 and int(sz[1]) > 0:
        return {
            "x": int(pos[0]),
            "y": int(pos[1]),
            "width": int(sz[0]),
            "height": int(sz[1]),
        }
    return None


def _resolve_multi_stream_region(
    session: Any,
    stream_idx: int,
    monitor: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Backward-compatible private alias for pre-public-API consumers."""
    return resolve_multi_stream_region(session, stream_idx, monitor)


def _build_screencast_extra(
    session: Any,
    stream_idx: int,
    multi_stream: bool,
    monitor: dict[str, Any] | None,
    crop_region: tuple[int, int, int, int] | None,
    region_local: dict[str, int] | None,
) -> dict[str, Any]:
    extra: dict[str, Any] = {
        "method": "portal-screencast",
        "screencast_nodes": session.node_ids,
        "screencast_stream_index": stream_idx,
    }
    if multi_stream:
        extra["method"] = "portal-screencast+stream"
        extra["screencast_multi_stream"] = True
        stream_region = resolve_multi_stream_region(session, stream_idx, monitor)
        if stream_region is not None:
            extra["region"] = stream_region
            extra["screencast_stream"] = True
    elif crop_region is not None:
        extra["region"] = {
            "x": crop_region[0],
            "y": crop_region[1],
            "width": crop_region[2],
            "height": crop_region[3],
        }
        if region_local is not None:
            extra["region_local"] = region_local
            extra["region_cropped_client"] = True
    else:
        extra["screencast_full_frame"] = True
        stream_region = screencast_stream_region(session)
        if stream_region is not None:
            extra["region"] = stream_region
            extra["screencast_stream"] = True
    return extra


def _maybe_fallback_stream_0(
    session: Any,
    png: bytes,
    stream_idx: int,
    monitor: dict[str, Any] | None,
    errors: list[str],
) -> tuple[bytes, int, bool]:
    """If the assigned stream gave a small/blank frame, fall back to stream 0 + crop."""
    w, h = png_dimensions(png)
    monitor_name = (monitor or {}).get("name") if monitor else None
    if monitor is None or (w >= 200 and h >= 200 and not is_blank_png(png)):
        return png, stream_idx, session_has_multiple_streams(session)
    if stream_idx == 0:
        return png, stream_idx, session_has_multiple_streams(session)
    errors.append(
        f"portal-screencast: stream {stream_idx} for {monitor_name} gave small/blank {w}x{h}; "
        "falling back to index 0 + crop (common with All Screens + complex/rotated layouts)"
    )
    png0 = _capture_screencast_png(session, 0, errors)
    if png0 is not None:
        return png0, 0, False  # force crop path on the "full" stream
    return png, stream_idx, session_has_multiple_streams(session)


def try_screencast_capture(
    screencast_session: Any,
    region: tuple[int, int, int, int] | None,
    errors: list[str],
    *,
    monitor: dict[str, Any] | None = None,
    all_monitors: list[dict[str, Any]] | None = None,
    display: str | None = None,
) -> tuple[bytes, dict[str, Any]] | None:
    try:
        session = _resolve_active_session(screencast_session, errors)
        if session is None:
            return None

        stream_idx = (
            screencast_stream_index_for_monitor(session, monitor, all_monitors=all_monitors)
            if monitor is not None
            else 0
        )
        orig_png = _capture_screencast_png(session, stream_idx, errors)
        if orig_png is None:
            return None

        png, stream_idx, multi_stream = _maybe_fallback_stream_0(
            session, orig_png, stream_idx, monitor, errors
        )

        png, crop_region, region_local = _maybe_crop_screencast_png(
            session, png, region, multi_stream, monitor, display
        )

        if is_blank_png(png):
            invalidate_screencast_session(session)
            errors.append(
                "portal-screencast: blank frame (stale ScreenCast — run: vdisplay agent screencast start)"
            )
            return None

        extra = _build_screencast_extra(
            session, stream_idx, multi_stream, monitor, crop_region, region_local
        )
        if stream_idx == 0 and png is not orig_png:
            extra["stream_fallback_to_0"] = True
            extra.setdefault("warnings", []).append("used stream 0 + crop because preferred stream was small/blank")
        return png, extra
    except VDisplayError as exc:
        errors.append(f"portal-screencast: {exc}")
        return None


def _capture_multi_stream_monitors(
    display: str,
    monitors: list[dict[str, Any]],
    output_dir: Path,
    screencast_session: Any,
) -> tuple[list[dict[str, Any]], list[str]] | None:
    stream_map = screencast_stream_map(screencast_session, monitors)
    captures: list[dict[str, Any]] = []
    warnings: list[str] = []
    for index, monitor in enumerate(monitors, start=1):
        name = str(monitor.get("name") or f"monitor-{index}")
        stream_idx = stream_map.get(name, 0)
        png = _capture_screencast_png_via_keeper_or_direct(
            screencast_session, stream_idx, warnings, timeout_s=30.0
        )
        if png is None:
            continue
        if is_blank_png(png):
            invalidate_screencast_session(screencast_session)
            raise VDisplayError("screencast capture blank — run: vdisplay agent screencast start")
        out_path = output_dir / f"{name}.png"
        out_path.write_bytes(png)
        stream_region = screencast_stream_region_for_monitor(screencast_session, monitor)
        meta: dict[str, Any] = {
            "path": str(out_path.resolve()),
            "bytes": len(png),
            "display": display,
            "source": name,
            "monitor": index,
            "method": "portal-screencast+stream",
            "monitor_index": index,
            "monitor_name": name,
            "screencast_stream_index": stream_idx,
            "screencast_multi_stream": True,
        }
        if stream_region is not None:
            meta["region"] = stream_region
            meta["screencast_stream"] = True
        w, h = png_dimensions(png)
        if w > 0 and h > 0:
            meta["width"] = w
            meta["height"] = h
        captures.append(meta)
    if not captures:
        return None
    return captures, warnings


def _resolve_single_stream_crop(
    full_png: bytes,
    region: tuple[int, int, int, int] | None,
    screencast_session: Any,
    monitor: dict[str, Any],
    display: str,
    full_saved: bool,
    warnings: list[str],
    name: str,
) -> tuple[bytes, str, tuple[int, int, int, int] | None, bool]:
    png = full_png
    method = "portal-screencast"
    crop_region = None
    if region is not None:
        crop_meta = build_screencast_crop_meta(screencast_session, full_png, monitor=monitor)
        cropped, local_region = crop_global_region_from_screencast(
            full_png, region, crop_meta, display=display
        )
        if local_region is not None:
            png = cropped
            method = "portal-screencast+crop"
            crop_region = region
        elif not full_saved:
            method = "portal-screencast+full"
            warnings.append(
                f"{name}: crop outside ScreenCast stream — saved full portal frame as {name}.png"
            )
            full_saved = True
        else:
            warnings.append(
                f"{name}: skipped (not in active ScreenCast stream; "
                "pick All Screens in portal or capture monitors individually)"
            )
            return png, method, crop_region, full_saved  # signals skip via crop_region=None
    return png, method, crop_region, full_saved


def _build_single_stream_meta(
    png: bytes,
    out_path: Path,
    display: str,
    name: str,
    index: int,
    method: str,
    crop_region: tuple[int, int, int, int] | None,
    screencast_session: Any,
) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "path": str(out_path.resolve()),
        "bytes": len(png),
        "display": display,
        "source": name,
        "monitor": index,
        "method": method,
        "monitor_index": index,
        "monitor_name": name,
    }
    if crop_region is not None:
        meta["region"] = {
            "x": crop_region[0],
            "y": crop_region[1],
            "width": crop_region[2],
            "height": crop_region[3],
        }
    else:
        meta["screencast_full_frame"] = True
        stream_region = screencast_stream_region(screencast_session)
        if stream_region is not None:
            meta["region"] = stream_region
            meta["screencast_stream"] = True
    w, h = png_dimensions(png)
    if w > 0 and h > 0:
        meta["width"] = w
        meta["height"] = h
    return meta


def _capture_single_stream_monitors(
    display: str,
    monitors: list[dict[str, Any]],
    output_dir: Path,
    screencast_session: Any,
    *,
    monitor_region_fn,
) -> tuple[list[dict[str, Any]], list[str]] | None:
    full_png = _capture_screencast_png_via_keeper_or_direct(
        screencast_session, 0, [], timeout_s=30.0
    )
    if full_png is None:
        return None
    if is_blank_png(full_png):
        invalidate_screencast_session(screencast_session)
        raise VDisplayError("screencast capture blank — run: vdisplay agent screencast start")

    captures: list[dict[str, Any]] = []
    warnings: list[str] = []
    full_saved = False

    for index, monitor in enumerate(monitors, start=1):
        name = str(monitor.get("name") or f"monitor-{index}")
        region = monitor_region_fn(display, name)
        png, method, crop_region, full_saved = _resolve_single_stream_crop(
            full_png, region, screencast_session, monitor, display, full_saved, warnings, name
        )
        if crop_region is None and region is not None and full_saved:
            # skip case already handled inside _resolve_single_stream_crop
            continue

        out_path = output_dir / f"{name}.png"
        out_path.write_bytes(png)
        meta = _build_single_stream_meta(
            png, out_path, display, name, index, method, crop_region, screencast_session
        )
        captures.append(meta)

    if not captures:
        return None
    return captures, warnings


def capture_all_from_screencast(
    display: str,
    monitors: list[dict[str, Any]],
    output_dir: Path,
    screencast_session: Any,
    *,
    monitor_region_fn,
) -> tuple[list[dict[str, Any]], list[str]] | None:
    if screencast_session is None or not screencast_session.is_ready:
        return None

    if session_has_multiple_streams(screencast_session):
        return _capture_multi_stream_monitors(display, monitors, output_dir, screencast_session)

    return _capture_single_stream_monitors(
        display, monitors, output_dir, screencast_session, monitor_region_fn=monitor_region_fn
    )
