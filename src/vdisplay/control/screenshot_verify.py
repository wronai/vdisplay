"""Screenshot-based verify-after-action (vision complement to AT-SPI diff)."""

from __future__ import annotations

import io
import tempfile
from pathlib import Path
from typing import Any, Callable

from ..exceptions import VDisplayError
from .models import ControlBounds, ControlNode

CaptureFn = Callable[..., bytes]


def _region_from_bounds(bounds: ControlBounds, *, padding: int = 12) -> tuple[int, int, int, int]:
    return (
        max(0, bounds.x - padding),
        max(0, bounds.y - padding),
        bounds.width + padding * 2,
        bounds.height + padding * 2,
    )


def enrich_screencast_stream_meta(meta: dict[str, Any]) -> dict[str, Any]:
    """Attach portal stream position/size when capture used a full ScreenCast frame."""
    meta = dict(meta)
    if meta.get("region") or not meta.get("screencast_full_frame"):
        return meta
    stream_region = _resolve_screencast_stream_region()
    if stream_region is not None:
        meta["region"] = stream_region
        meta["screencast_stream"] = True
    return meta


def _resolve_screencast_stream_region() -> dict[str, int] | None:
    from ..capture.portal_screencast import get_active_screencast, screencast_stream_region

    region = screencast_stream_region(get_active_screencast())
    if region is not None:
        return region
    return _region_from_agent_screencast_status()


def _region_from_agent_screencast_status() -> dict[str, int] | None:
    from ..agent_config import resolve_agent_url
    from ..client import AgentClient

    agent_url = resolve_agent_url(allow_auto=True)
    if not agent_url:
        return None
    try:
        status = AgentClient(agent_url).screencast_status()
    except VDisplayError:
        return None
    payload = status.get("data") if isinstance(status.get("data"), dict) else status
    streams = list((payload or {}).get("streams") or [])
    if not streams:
        return None
    properties = streams[0].get("properties") or {}
    position = properties.get("position") or [0, 0]
    size = properties.get("size") or []
    if len(position) < 2 or len(size) < 2:
        return None
    width = int(size[0])
    height = int(size[1])
    if width <= 0 or height <= 0:
        return None
    return {
        "x": int(position[0]),
        "y": int(position[1]),
        "width": width,
        "height": height,
    }


def capture_control_screenshot(
    *,
    display: str | None = None,
    target: ControlNode | None = None,
    capture_fn: CaptureFn | None = None,
) -> tuple[bytes, dict[str, Any]]:
    """Capture PNG bytes for verify (full display or padded target region)."""
    region = _target_region(target)
    if capture_fn is not None:
        return capture_fn(display=display, region=region), {"region": region, "method": "injected"}

    agent_capture = _capture_via_agent(display=display, region=region)
    if agent_capture is not None:
        return _maybe_crop_capture(agent_capture, region)

    from ..capture.host import capture_host_png

    png, meta = capture_host_png(display=display, region=region)
    meta = enrich_screencast_stream_meta(dict(meta))
    return _maybe_crop_capture((png, meta), region)


def _target_region(target: ControlNode | None) -> tuple[int, int, int, int] | None:
    if target is None or target.bounds is None:
        return None
    if target.bounds.width <= 0 or target.bounds.height <= 0:
        return None
    return _region_from_bounds(target.bounds)


def _maybe_crop_capture(
    payload: tuple[bytes, dict[str, Any]],
    region: tuple[int, int, int, int] | None,
) -> tuple[bytes, dict[str, Any]]:
    png, meta = payload
    meta = dict(meta)
    if region is not None:
        meta["requested_region"] = {
            "x": region[0],
            "y": region[1],
            "width": region[2],
            "height": region[3],
        }
    if region is None or not meta.get("screencast_full_frame"):
        if region is not None and "region" not in meta:
            meta["region"] = meta["requested_region"]
        return png, meta
    from ..capture.linux_xwd import _crop_png, is_blank_png

    cropped = _crop_png(png, region)
    if is_blank_png(cropped):
        meta["region_crop_failed"] = True
        return png, meta
    meta["region"] = meta["requested_region"]
    meta["screencast_full_frame"] = False
    meta["region_cropped_client"] = True
    return cropped, meta


def _capture_via_agent(
    *,
    display: str | None,
    region: tuple[int, int, int, int] | None,
) -> tuple[bytes, dict[str, Any]] | None:
    """Use vdisplay-agent ScreenCast when the CLI process has no local portal session."""
    from ..agent_config import resolve_agent_url
    from ..client import AgentClient

    agent_url = resolve_agent_url(allow_auto=True)
    if not agent_url:
        return None
    kwargs: dict[str, Any] = {"display": display}
    if region is not None:
        kwargs["region"] = {
            "x": region[0],
            "y": region[1],
            "width": region[2],
            "height": region[3],
        }
    try:
        client = AgentClient(agent_url)
        with tempfile.TemporaryDirectory(prefix="vdisplay-verify-") as tmpdir:
            output = str(Path(tmpdir) / "frame.png")
            png, meta = client.capture_png_bytes(output=output, **kwargs)
    except VDisplayError:
        return None
    meta = enrich_screencast_stream_meta(dict(meta))
    meta["method"] = meta.get("method") or "agent-screencast"
    if region is not None:
        meta["region"] = kwargs["region"]
    return png, meta


def diff_png_bytes(
    before: bytes,
    after: bytes,
    *,
    region: tuple[int, int, int, int] | None = None,
    min_changed_ratio: float = 0.001,
    min_changed_pixels: int = 0,
) -> dict[str, Any]:
    """Compare two PNG payloads and report whether they differ meaningfully."""
    compare_region = region
    if compare_region is not None:
        from ..capture.linux_xwd import _crop_png, is_blank_png

        before_crop = _crop_png(before, compare_region)
        after_crop = _crop_png(after, compare_region)
        if not is_blank_png(before_crop) and not is_blank_png(after_crop):
            before = before_crop
            after = after_crop
        else:
            compare_region = None

    if before == after:
        return {
            "verified": False,
            "changed_ratio": 0.0,
            "changed_pixels": 0,
            "total_pixels": 0,
            "method": "bytes",
            "compare_region": compare_region,
        }
    try:
        from PIL import Image
    except ImportError:
        return {
            "verified": True,
            "changed_ratio": 1.0,
            "changed_pixels": None,
            "total_pixels": None,
            "method": "bytes",
            "compare_region": compare_region,
        }

    before_image = Image.open(io.BytesIO(before)).convert("RGB")
    after_image = Image.open(io.BytesIO(after)).convert("RGB")
    if before_image.size != after_image.size:
        after_image = after_image.resize(before_image.size)

    width, height = before_image.size
    total_pixels = width * height
    changed_pixels = 0
    before_pixels = before_image.get_flattened_data()
    after_pixels = after_image.get_flattened_data()
    for left, right in zip(before_pixels, after_pixels, strict=False):
        if left != right:
            changed_pixels += 1
    changed_ratio = changed_pixels / total_pixels if total_pixels else 0.0
    verified = changed_pixels > 0 if compare_region is not None else False
    if not verified:
        verified = changed_pixels >= min_changed_pixels or changed_ratio >= min_changed_ratio
    return {
        "verified": verified,
        "changed_ratio": round(changed_ratio, 6),
        "changed_pixels": changed_pixels,
        "total_pixels": total_pixels,
        "method": "pil",
        "compare_region": compare_region,
    }


def verify_screenshot_pair(
    before: bytes,
    after: bytes,
    *,
    region: tuple[int, int, int, int] | None = None,
    min_changed_ratio: float = 0.001,
    min_changed_pixels: int = 50,
) -> dict[str, Any]:
    """Build verification payload for before/after screenshots."""
    diff = diff_png_bytes(
        before,
        after,
        region=region,
        min_changed_ratio=min_changed_ratio,
        min_changed_pixels=min_changed_pixels,
    )
    return {
        "verified": diff["verified"],
        "changed_ratio": diff["changed_ratio"],
        "changed_pixels": diff.get("changed_pixels"),
        "total_pixels": diff.get("total_pixels"),
        "method": diff["method"],
        "min_changed_ratio": min_changed_ratio,
        "min_changed_pixels": min_changed_pixels,
        "compare_region": diff.get("compare_region"),
    }
