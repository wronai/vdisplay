"""Map web console monitor clicks to desktop pointer actions."""

from __future__ import annotations

import struct
import time
from pathlib import Path
from typing import Any

from vdisplay.capture.coordinate_map import global_pointer_coords
from vdisplay.control.screenshot_verify import enrich_screencast_stream_meta, global_point_in_stream_bounds
from vdisplay.control.timing import control_pointer_settle_seconds
from vdisplay.discovery import list_monitors, resolve_host_display
from vdisplay.exceptions import VDisplayError
from vdisplay.input.resolve import resolve_pointer_input


def _png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        handle.seek(16)
        chunk = handle.read(8)
    if len(chunk) != 8:
        raise VDisplayError(f"invalid png header: {path}")
    width, height = struct.unpack(">II", chunk)
    return int(width), int(height)


def _monitor_by_name(display: str | None, name: str) -> dict[str, Any] | None:
    resolved = resolve_host_display(display)
    for monitor in list_monitors(resolved):
        if str(monitor.get("name") or monitor.get("label") or "") == name:
            return monitor
    return None


def _resolve_local_coords(
    x: float,
    y: float,
    *,
    coord_space: str,
    png_w: int,
    png_h: int,
) -> tuple[int, int]:
    space = (coord_space or "png").strip().lower()
    if space == "normalized":
        if png_w <= 0 or png_h <= 0:
            raise VDisplayError("png dimensions unavailable for normalized coords")
        return int(x * png_w), int(y * png_h)
    if space == "png":
        return int(x), int(y)
    raise VDisplayError(f"unsupported coord_space: {coord_space}")


def build_monitor_capture_meta(
    capture_meta: dict[str, Any],
    *,
    monitor: dict[str, Any],
    png_path: Path,
) -> dict[str, Any]:
    """Merge host capture meta with monitor geometry for coordinate_map."""
    png_w, png_h = _png_dimensions(png_path)
    meta = enrich_screencast_stream_meta(dict(capture_meta))
    meta.setdefault("width", png_w)
    meta.setdefault("height", png_h)
    meta.setdefault("source", monitor.get("name") or monitor.get("label"))
    meta.setdefault("monitor_name", meta.get("source"))
    meta.setdefault("rotation", monitor.get("rotation") or "normal")
    if not meta.get("region") and not meta.get("screencast_stream_region"):
        meta["region"] = {
            "x": int(monitor.get("x") or 0),
            "y": int(monitor.get("y") or 0),
            "width": int(monitor.get("width") or png_w),
            "height": int(monitor.get("height") or png_h),
        }
    return meta


def pointer_click_at_monitor(
    *,
    monitor_name: str,
    x: float,
    y: float,
    capture_meta: dict[str, Any],
    png_path: Path,
    coord_space: str = "png",
    button: int = 1,
    display: str | None = None,
) -> dict[str, Any]:
    """Click desktop at PNG-local coordinates on a named monitor."""
    monitor = _monitor_by_name(display, monitor_name)
    if monitor is None:
        raise VDisplayError(f"monitor not found: {monitor_name}")
    if not png_path.is_file():
        raise VDisplayError(f"capture png missing: {png_path}")

    meta = build_monitor_capture_meta(capture_meta, monitor=monitor, png_path=png_path)
    png_w = int(meta.get("width") or 0)
    png_h = int(meta.get("height") or 0)
    local_x, local_y = _resolve_local_coords(x, y, coord_space=coord_space, png_w=png_w, png_h=png_h)

    if local_x < 0 or local_y < 0 or local_x >= png_w or local_y >= png_h:
        raise VDisplayError(f"click outside png bounds: ({local_x},{local_y}) in {png_w}x{png_h}")

    gx, gy, mapping = global_pointer_coords(local_x, local_y, meta, display=display)
    if not global_point_in_stream_bounds(gx, gy, meta):
        raise VDisplayError(
            f"mapped point ({gx},{gy}) outside ScreenCast stream — pick monitor in portal or use All Screens"
        )

    inp, method = resolve_pointer_input(display=display)
    inp.move(gx, gy)
    inp.click(button)
    settle_s = control_pointer_settle_seconds()
    if settle_s:
        time.sleep(settle_s)

    return {
        "ok": True,
        "monitor": monitor_name,
        "method": method,
        "button": int(button),
        "coord_space": coord_space,
        "local_x": local_x,
        "local_y": local_y,
        "global_x": gx,
        "global_y": gy,
        "coord_mapping": mapping,
        "png_width": png_w,
        "png_height": png_h,
    }
