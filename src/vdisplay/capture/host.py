"""Host desktop capture via driver-level providers (DRM/fbdev/XCB/X11) and mirror."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ..capture.linux_xwd import _crop_png, _is_wayland_session, capture_display_png, is_blank_png
from ..capture.providers.engine import capture_full_png
from ..discovery import _looks_like_xvfb_only, list_monitors, resolve_host_display
from ..exceptions import BackendNotAvailableError, VDisplayError


def _wayland_host_session(display: str) -> bool:
    return _is_wayland_session() and not _looks_like_xvfb_only(display)


def _monitor_source_name(display: str, monitor: int, source: str) -> str:
    monitors = list_monitors(display)
    if not monitors:
        raise BackendNotAvailableError(f"No monitors on {display}")

    normalized = (source or "primary").strip().lower()
    if normalized not in {"primary", "default"}:
        for item in monitors:
            if str(item.get("name", "")).lower() == normalized:
                return str(item["name"])
        return source

    if 1 <= monitor <= len(monitors):
        return str(monitors[monitor - 1]["name"])

    for item in monitors:
        if item.get("primary"):
            return str(item["name"])
    return str(monitors[0]["name"])


def resolve_window_region(
    display: str,
    *,
    match_title: str | None = None,
    window_id: str | None = None,
    match_class: str | None = None,
    match_pid: int | None = None,
    match_app: str | None = None,
) -> tuple[tuple[int, int, int, int], dict[str, Any]]:
    """Resolve absolute root-window region for a visible window."""
    from ..windows import find_windows, pick_best_window

    window: dict[str, Any] | None = None
    if window_id:
        for candidate in find_windows(display, apps_only=False):
            if str(candidate.get("window_id")) == str(window_id):
                window = candidate
                break
        if window is None:
            raise VDisplayError(f"window not found: {window_id}")
    else:
        matches = find_windows(
            display,
            match_title=match_title,
            match_class=match_class,
            match_pid=match_pid,
            match_app=match_app,
            apps_only=True,
        )
        window = pick_best_window(matches)
        if window is None:
            raise VDisplayError(
                "no window matched relay screenshot filters — "
                "run: vdisplay windows --apps-only"
            )

    x, y = window.get("x"), window.get("y")
    width, height = window.get("width"), window.get("height")
    if None in (x, y, width, height) or int(width) <= 0 or int(height) <= 0:
        raise VDisplayError("window geometry unavailable for relay screenshot")
    region = (int(x), int(y), int(width), int(height))
    return region, {
        "window_id": window.get("window_id"),
        "title": window.get("title") or window.get("name"),
        "app_label": window.get("app_label"),
        "pid": window.get("pid"),
        "region": {
            "x": region[0],
            "y": region[1],
            "width": region[2],
            "height": region[3],
        },
    }


def _monitor_capture_region(display: str, output_name: str) -> tuple[int, int, int, int] | None:
    for output in list_monitors(display):
        if output.get("name") != output_name:
            continue
        x, y = output.get("x"), output.get("y")
        width, height = output.get("width"), output.get("height")
        if None in (x, y, width, height):
            return None
        return int(x), int(y), int(width), int(height)
    return None


def _capture_all_from_driver_full(
    display: str,
    monitors: list[dict[str, Any]],
    output_dir: Path,
) -> list[dict[str, Any]] | None:
    try:
        result = capture_full_png(display)
    except VDisplayError:
        return None

    captures: list[dict[str, Any]] = []
    for index, monitor in enumerate(monitors, start=1):
        name = str(monitor.get("name") or f"monitor-{index}")
        region = _monitor_capture_region(display, name)
        if region is None:
            raise VDisplayError(f"monitor region missing for {name}")
        png = _crop_png(result.png, region)
        if is_blank_png(png):
            raise VDisplayError(f"driver crop blank for {name}")
        out_path = output_dir / f"{name}.png"
        out_path.write_bytes(png)
        meta: dict[str, Any] = {
            "path": str(out_path.resolve()),
            "bytes": len(png),
            "display": display,
            "source": name,
            "monitor": index,
            "method": f"{result.provider}+crop",
            "monitor_index": index,
            "monitor_name": name,
            "region": {
                "x": region[0],
                "y": region[1],
                "width": region[2],
                "height": region[3],
            },
        }
        try:
            from PIL import Image

            with Image.open(out_path) as image:
                meta["width"] = image.width
                meta["height"] = image.height
        except Exception:
            pass
        captures.append(meta)
    return captures


def _capture_all_from_screencast(
    display: str,
    monitors: list[dict[str, Any]],
    output_dir: Path,
    screencast_session: Any,
) -> tuple[list[dict[str, Any]], list[str]] | None:
    if screencast_session is None or not screencast_session.is_ready:
        return None
    try:
        full_png = screencast_session.capture_png()
    except VDisplayError:
        return None
    if is_blank_png(full_png):
        from .portal_screencast import invalidate_screencast_session

        invalidate_screencast_session(screencast_session)
        raise VDisplayError(
            "screencast capture blank — run: vdisplay agent screencast start"
        )

    captures: list[dict[str, Any]] = []
    warnings: list[str] = []
    full_saved = False

    for index, monitor in enumerate(monitors, start=1):
        name = str(monitor.get("name") or f"monitor-{index}")
        region = _monitor_capture_region(display, name)
        png = full_png
        method = "portal-screencast"
        crop_region = None

        if region is not None:
            cropped = _crop_png(full_png, region)
            if not is_blank_png(cropped):
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
                continue

        out_path = output_dir / f"{name}.png"
        out_path.write_bytes(png)
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
        try:
            from PIL import Image

            with Image.open(out_path) as image:
                meta["width"] = image.width
                meta["height"] = image.height
        except Exception:
            pass
        captures.append(meta)

    if not captures:
        return None
    return captures, warnings


def _try_screencast_capture(screencast_session, region, errors) -> tuple[bytes, dict[str, Any]] | None:
    try:
        from .portal_screencast import get_active_screencast
        from .linux_xwd import _is_wayland_session

        session = screencast_session or get_active_screencast()
        if session is None or not session.is_ready:
            hint = "vdisplay agent screencast start"
            if _is_wayland_session():
                hint = "vdisplay-agent serve, then vdisplay agent screencast start (or export VDISPLAY_AGENT_URL=http://127.0.0.1:8765)"
            errors.append(f"portal-screencast: no active session (run: {hint})")
            return None
        png = session.capture_png()
        crop_region = region
        if crop_region is not None:
            cropped = _crop_png(png, crop_region)
            if not is_blank_png(cropped):
                png = cropped
            else:
                crop_region = None
        if is_blank_png(png):
            from .portal_screencast import invalidate_screencast_session
            invalidate_screencast_session(session)
            errors.append("portal-screencast: blank frame (stale ScreenCast — run: vdisplay agent screencast start)")
            return None
        extra = {"method": "portal-screencast", "screencast_nodes": session.node_ids}
        if crop_region is not None:
            extra["region"] = {
                "x": crop_region[0], "y": crop_region[1], 
                "width": crop_region[2], "height": crop_region[3]
            }
        else:
            extra["screencast_full_frame"] = True
        return png, extra
    except VDisplayError as exc:
        errors.append(f"portal-screencast: {exc}")
        return None

def _try_mirror_capture(monitors, source_name, target, resolved, errors) -> tuple[bytes, dict[str, Any]] | None:
    if len(monitors) < 2:
        return None
    try:
        from ..api import MirrorSession

        session = MirrorSession.create(source=source_name, target=target, display=resolved)
        session.start()
        try:
            png = session.screenshot_bytes()
            if is_blank_png(png):
                errors.append("mirror: blank frame")
                return None
            info = session.info()
            return png, {"method": "mirror", "target": info.get("target") or target, "session": info}
        finally:
            session.stop()
    except (VDisplayError, BackendNotAvailableError) as exc:
        errors.append(f"mirror: {exc}")
        return None


def _try_driver_capture(resolved: str, region: tuple[int, int, int, int] | None, errors: list[str]) -> tuple[bytes, dict[str, Any]] | None:
    if region is not None:
        try:
            png = capture_display_png(resolved, region=region)
            if not is_blank_png(png):
                return png, {
                    "method": "monitor-region",
                    "region": {
                        "x": region[0], "y": region[1], "width": region[2], "height": region[3]
                    }
                }
            errors.append("monitor-region: blank frame")
        except VDisplayError as exc:
            errors.append(f"monitor-region: {exc}")

    try:
        png = capture_display_png(resolved)
        if not is_blank_png(png):
            return png, {"method": "full-display"}
        errors.append("full-display: blank frame")
    except VDisplayError as exc:
        errors.append(f"full-display: {exc}")
    
    return None


def capture_host_png(
    *,
    monitor: int = 1,
    display: str | None = None,
    source: str | None = None,
    target: str | None = None,
    prefer_mirror: bool = False,
    screencast_session=None,
    region: tuple[int, int, int, int] | None = None,
) -> tuple[bytes, dict[str, Any]]:
    resolved = resolve_host_display(display or os.environ.get("DISPLAY"))
    source_name = _monitor_source_name(resolved, monitor, source or "primary")
    monitors = list_monitors(resolved)
    meta: dict[str, Any] = {
        "display": resolved, "source": source_name, "monitor": monitor, 
        "method": "", "target": target
    }
    errors: list[str] = []
    region = region or _monitor_capture_region(resolved, source_name)

    screencast_hit = _try_screencast_capture(screencast_session, region, errors)
    if screencast_hit is not None:
        png, extra = screencast_hit
        meta.update(extra)
        return png, meta

    if _wayland_host_session(resolved):
        raise VDisplayError(_host_capture_error(resolved, source_name, errors))

    if prefer_mirror:
        mirror_hit = _try_mirror_capture(monitors, source_name, target, resolved, errors)
        if mirror_hit is not None:
            png, extra = mirror_hit
            meta.update(extra)
            return png, meta

    driver_hit = _try_driver_capture(resolved, region, errors)
    if driver_hit is not None:
        png, extra = driver_hit
        meta.update(extra)
        return png, meta

    if not prefer_mirror:
        mirror_hit = _try_mirror_capture(monitors, source_name, target, resolved, errors)
        if mirror_hit is not None:
            png, extra = mirror_hit
            meta.update(extra)
            return png, meta

    raise VDisplayError(_host_capture_error(resolved, source_name, errors))


def _host_capture_error(display: str, source: str, errors: list[str]) -> str:
    from .linux_xwd import _is_wayland_session

    message = (
        "vdisplay host capture failed (blank or unavailable). "
        f"DISPLAY={display}, source={source}. "
        f"Tried: {'; '.join(errors) or 'no strategy'}."
    )
    if _is_wayland_session():
        message += (
            " On GNOME Wayland use the local agent with a persistent ScreenCast session: "
            "`vdisplay-agent serve`, then `vdisplay agent screencast start`, "
            "then retry screenshot (auto-detects http://127.0.0.1:8765 when running)."
        )
    else:
        message += (
            " For driver-level host capture add user to `video` group (DRM/fbdev), "
            "or use `vdisplay virtual screenshot` for owned framebuffers."
        )
    return message


def capture_host_to_file(
    path: str | Path,
    *,
    monitor: int = 1,
    display: str | None = None,
    source: str | None = None,
    target: str | None = None,
    prefer_mirror: bool = False,
    screencast_session=None,
    region: tuple[int, int, int, int] | None = None,
) -> dict[str, Any]:
    """Write host capture PNG to path; return metadata dict."""
    out = Path(path).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    png, meta = capture_host_png(
        monitor=monitor,
        display=display,
        source=source,
        target=target,
        prefer_mirror=prefer_mirror,
        screencast_session=screencast_session,
        region=region,
    )
    out.write_bytes(png)
    meta["path"] = str(out.resolve())
    meta["bytes"] = len(png)
    try:
        from ..capture.linux_xwd import PNG_SIGNATURE

        if png[: len(PNG_SIGNATURE)] == PNG_SIGNATURE:
            from PIL import Image

            with Image.open(out) as image:
                meta["width"] = image.width
                meta["height"] = image.height
    except Exception:
        pass
    return meta


def _capture_individual_monitors(
    monitors: list[dict[str, Any]], resolved: str, output_dir: Path | None, 
    target: str | None, method: str, prefer_mirror: bool, screencast_session
) -> list[dict[str, Any]]:
    captures: list[dict[str, Any]] = []
    for index, monitor in enumerate(monitors, start=1):
        name = str(monitor.get("name") or f"monitor-{index}")
        if output_dir is not None:
            meta = capture_host_to_file(
                output_dir / f"{name}.png", monitor=index, display=resolved,
                source=name, target=target, prefer_mirror=prefer_mirror,
                screencast_session=screencast_session
            )
        else:
            png, meta = capture_host_png(
                monitor=index, display=resolved, source=name,
                target=target, prefer_mirror=prefer_mirror,
                screencast_session=screencast_session
            )
            meta = dict(meta)
            meta["bytes"] = len(png)
            
        meta["monitor_index"] = index
        meta["monitor_name"] = name
        meta["method_requested"] = method
        captures.append(meta)
    return captures


def _try_bulk_capture(
    resolved: str, monitors: list[dict[str, Any]], output_dir: Path | None,
    method: str, prefer_mirror: bool, screencast_session
) -> tuple[list[dict[str, Any]], list[str]] | None:
    if output_dir is None or prefer_mirror:
        return None
        
    warnings: list[str] = []
    if screencast_session is not None and screencast_session.is_ready:
        bulk_sc = _capture_all_from_screencast(resolved, monitors, output_dir, screencast_session)
        if bulk_sc is not None:
            captures, warnings = bulk_sc
            for item in captures:
                item["method_requested"] = method
            return captures, warnings
            
    if screencast_session is None or not screencast_session.is_ready:
        if _wayland_host_session(resolved):
            raise VDisplayError(
                "Wayland host capture requires an active ScreenCast session — "
                "run: vdisplay agent serve, then vdisplay agent screencast start"
            )
        bulk = _capture_all_from_driver_full(resolved, monitors, output_dir)
        if bulk is not None:
            for item in bulk:
                item["method_requested"] = method
            return bulk, warnings
            
    return None


def capture_all_monitors(
    *,
    display: str | None = None,
    out_dir: str | Path | None = None,
    target: str | None = None,
    method: str = "auto",
    prefer_mirror: bool = False,
    screencast_session=None,
) -> dict[str, Any]:
    resolved = resolve_host_display(display or os.environ.get("DISPLAY"))
    monitors = list_monitors(resolved)
    if not monitors:
        raise BackendNotAvailableError(f"No monitors on {resolved}")

    if screencast_session is None:
        try:
            from .portal_screencast import get_active_screencast
            screencast_session = get_active_screencast()
        except Exception:
            screencast_session = None

    output_dir = Path(out_dir).expanduser() if out_dir else None
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        
    bulk_result = _try_bulk_capture(resolved, monitors, output_dir, method, prefer_mirror, screencast_session)
    if bulk_result is not None:
        return {"captures": bulk_result[0], "warnings": bulk_result[1], "count": len(bulk_result[0])}

    captures = _capture_individual_monitors(
        monitors, resolved, output_dir, target, method, prefer_mirror, screencast_session
    )
    return {"captures": captures, "warnings": [], "count": len(captures)}
