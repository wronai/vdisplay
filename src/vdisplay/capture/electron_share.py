"""Optional Electron/browser screen-share capture provider.

This provider talks to a local Electron app that owns the GNOME portal
permission and exposes the latest shared frame over localhost.
"""

from __future__ import annotations

import io
import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

from ..exceptions import VDisplayError
from .linux_xwd import _crop_png, is_blank_png


_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_AUTO_PROBE_CACHE: tuple[float, bool] | None = None


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _falsy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"0", "false", "no", "off"}


def electron_share_enabled() -> bool:
    if bool(os.environ.get("VDISPLAY_ELECTRON_SHARE_URL")) or _truthy(
        os.environ.get("VDISPLAY_ELECTRON_SHARE")
    ):
        return True
    if _falsy(os.environ.get("VDISPLAY_ELECTRON_SHARE")) or _falsy(
        os.environ.get("VDISPLAY_ELECTRON_SHARE_AUTO")
    ):
        return False
    return electron_share_manager_available()


def electron_share_url() -> str:
    return (os.environ.get("VDISPLAY_ELECTRON_SHARE_URL") or "http://127.0.0.1:8799").rstrip("/")


def _probe_timeout_s() -> float:
    raw = os.environ.get("VDISPLAY_ELECTRON_SHARE_PROBE_TIMEOUT_S")
    try:
        return max(0.05, min(3.0, float(raw))) if raw else 0.35
    except (TypeError, ValueError):
        return 0.35


def electron_share_manager_available() -> bool:
    global _AUTO_PROBE_CACHE

    now = time.monotonic()
    if _AUTO_PROBE_CACHE is not None:
        cached_at, cached = _AUTO_PROBE_CACHE
        if now - cached_at < 1.0:
            return cached

    url = f"{electron_share_url()}/status"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=_probe_timeout_s()) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
    except Exception:
        _AUTO_PROBE_CACHE = (now, False)
        return False

    available = bool(
        isinstance(payload, dict)
        and payload.get("ok")
        and (
            payload.get("service") == "vdisplay-electron-share"
            or payload.get("url")
            or payload.get("instance")
        )
    )
    _AUTO_PROBE_CACHE = (now, available)
    return available


def _electron_share_timeout_s() -> float:
    raw = os.environ.get("VDISPLAY_ELECTRON_SHARE_TIMEOUT_S")
    try:
        return max(0.2, min(30.0, float(raw))) if raw else 2.0
    except (TypeError, ValueError):
        return 2.0


def _max_frame_age_ms() -> int:
    raw = os.environ.get("VDISPLAY_ELECTRON_SHARE_MAX_FRAME_AGE_MS")
    try:
        value = int(float(raw)) if raw is not None else 15000
    except (TypeError, ValueError):
        return 5000
    return max(0, min(300000, value))


def _frame_age_ms(status: dict[str, Any]) -> int | None:
    candidates: list[Any] = []
    frame = status.get("frame") if isinstance(status.get("frame"), dict) else {}
    if frame:
        candidates.append(frame.get("age_ms"))
    candidates.append(status.get("last_frame_age_ms"))

    for candidate in candidates:
        try:
            if candidate is not None:
                return int(float(candidate))
        except (TypeError, ValueError):
            continue
    return None


def _validate_fresh_frame_status(status: dict[str, Any]) -> None:
    if not status:
        return

    if status.get("sharing") is False:
        raise VDisplayError("manager is not sharing")

    max_age_ms = _max_frame_age_ms()
    if max_age_ms <= 0:
        return

    age_ms = _frame_age_ms(status)
    if age_ms is not None and age_ms > max_age_ms:
        raise VDisplayError(f"stale frame age_ms={age_ms} exceeds max_age_ms={max_age_ms}")


def _request_png() -> bytes:
    url = f"{electron_share_url()}/frame.png"
    req = urllib.request.Request(url, headers={"Accept": "image/png"})
    try:
        with urllib.request.urlopen(req, timeout=_electron_share_timeout_s()) as response:
            data = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace").strip()
        raise VDisplayError(f"{url}: HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise VDisplayError(f"{url}: {exc.reason}") from exc
    except TimeoutError as exc:
        raise VDisplayError(f"{url}: timed out") from exc

    if not data.startswith(_PNG_MAGIC):
        raise VDisplayError(f"{url}: response is not PNG")
    return data


def _request_status() -> dict[str, Any]:
    url = f"{electron_share_url()}/status"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=_electron_share_timeout_s()) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def electron_share_manager_status() -> dict[str, Any]:
    """Return passive Electron Share manager status, or empty dict when unavailable."""
    return _request_status()


def _png_size(png: bytes) -> tuple[int, int] | None:
    try:
        from PIL import Image

        with Image.open(io.BytesIO(png)) as image:
            return int(image.width), int(image.height)
    except Exception:
        return None


def _region_dict(region: tuple[int, int, int, int]) -> dict[str, int]:
    return {"x": region[0], "y": region[1], "width": region[2], "height": region[3]}


def _monitor_bbox_origin(monitors: list[dict[str, Any]] | None) -> tuple[int, int]:
    if not monitors:
        return 0, 0
    xs: list[int] = []
    ys: list[int] = []
    for monitor in monitors:
        try:
            xs.append(int(monitor.get("x") or 0))
            ys.append(int(monitor.get("y") or 0))
        except (TypeError, ValueError):
            continue
    return (min(xs) if xs else 0), (min(ys) if ys else 0)


def _fits(size: tuple[int, int] | None, region: tuple[int, int, int, int]) -> bool:
    if size is None:
        return True
    width, height = size
    x, y, region_width, region_height = region
    return x >= 0 and y >= 0 and x + region_width <= width and y + region_height <= height


def _bounds_tuple(display: dict[str, Any]) -> tuple[int, int, int, int] | None:
    bounds = display.get("bounds")
    if not isinstance(bounds, dict):
        return None
    try:
        return (
            int(bounds.get("x") or 0),
            int(bounds.get("y") or 0),
            int(bounds.get("width") or 0),
            int(bounds.get("height") or 0),
        )
    except (TypeError, ValueError):
        return None


def _scale_factor(display: dict[str, Any]) -> float:
    try:
        value = float(display.get("scaleFactor") or 1.0)
    except (TypeError, ValueError):
        return 1.0
    return value if value > 0 else 1.0


def _region_matches_display(
    region: tuple[int, int, int, int],
    display: dict[str, Any],
    *,
    tolerance: int = 2,
) -> bool:
    bounds = _bounds_tuple(display)
    if bounds is None:
        return False
    scale = _scale_factor(display)
    scaled = tuple(int(round(value / scale)) for value in region)
    return all(abs(scaled[index] - bounds[index]) <= tolerance for index in range(4))


def _display_for_monitor_region(
    region: tuple[int, int, int, int],
    displays: list[dict[str, Any]] | None,
) -> dict[str, Any] | None:
    for display in displays or []:
        if isinstance(display, dict) and _region_matches_display(region, display):
            return display
    return None


def _crop_for_monitor(
    png: bytes,
    region: tuple[int, int, int, int] | None,
    all_monitors: list[dict[str, Any]] | None,
    manager_status: dict[str, Any] | None = None,
) -> tuple[bytes, dict[str, Any]]:
    if region is None:
        return png, {}

    size = _png_size(png)
    x, y, width, height = region
    if size == (width, height):
        return png, {
            "region": _region_dict(region),
            "electron_share_crop": "single-monitor-frame",
        }

    status = manager_status if isinstance(manager_status, dict) else {}
    frame = status.get("frame") if isinstance(status.get("frame"), dict) else {}
    displays = status.get("displays") if isinstance(status.get("displays"), list) else []
    display = _display_for_monitor_region(region, displays)
    if display is not None:
        bounds = _bounds_tuple(display)
        display_id = str(display.get("id") or "")
        frame_display_id = str(frame.get("displayId") or "")
        if frame_display_id and display_id and frame_display_id != display_id:
            raise VDisplayError(
                "electron-share is sharing display "
                f"{frame_display_id}, but requested monitor region maps to display {display_id}"
            )
        if bounds is not None and size == (bounds[2], bounds[3]):
            return png, {
                "region": _region_dict(region),
                "electron_share_crop": "single-monitor-frame",
                "electron_share_display_id": display_id or None,
                "electron_share_scale_factor": _scale_factor(display),
            }

    origin_x, origin_y = _monitor_bbox_origin(all_monitors)
    candidates = [
        (x - origin_x, y - origin_y, width, height),
        region,
    ]
    for candidate in candidates:
        if not _fits(size, candidate):
            continue
        cropped = _crop_png(png, candidate)
        if not is_blank_png(cropped):
            return cropped, {
                "region": _region_dict(region),
                "electron_share_crop": "composite-monitor-region",
                "electron_share_frame_size": {
                    "width": size[0],
                    "height": size[1],
                }
                if size
                else None,
            }

    raise VDisplayError(
        f"shared frame size {size or 'unknown'} does not contain monitor region "
        f"{_region_dict(region)}"
    )


def try_electron_share_capture(
    region: tuple[int, int, int, int] | None,
    errors: list[str],
    *,
    monitor: dict[str, Any] | None = None,
    all_monitors: list[dict[str, Any]] | None = None,
    display: str | None = None,
) -> tuple[bytes, dict[str, Any]] | None:
    if not electron_share_enabled():
        return None

    try:
        manager_status = _request_status()
        _validate_fresh_frame_status(manager_status)
        png = _request_png()
        if is_blank_png(png):
            errors.append("electron-share: blank frame")
            return None
        png, crop_meta = _crop_for_monitor(png, region, all_monitors, manager_status)
        meta: dict[str, Any] = {
            "method": "electron-share",
            "electron_share_url": electron_share_url(),
        }
        if display:
            meta["display"] = display
        if monitor:
            meta["monitor_name"] = monitor.get("name")
        meta.update({k: v for k, v in crop_meta.items() if v is not None})
        return png, meta
    except VDisplayError as exc:
        errors.append(f"electron-share: {exc}")
        return None
