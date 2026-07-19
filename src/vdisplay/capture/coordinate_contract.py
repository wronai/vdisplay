"""Deterministic capture-coordinate contract and pure metadata normalization."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from importlib import resources
from typing import Any, Mapping

from .coordinate_rotation import region_rel_to_local

COORDINATE_MAP_V1 = "vdisplay.coordinate-map.v1"
_SCHEMA_RESOURCE = "coordinate-map-v1.schema.json"
_FALLBACK_META_KEYS = (
    "region",
    "rotation",
    "screencast_stream",
    "screencast_full_frame",
    "screencast_stream_region",
    "width",
    "height",
    "display_bounds",
)


def _positive_int(value: Any) -> int:
    try:
        parsed = int(value or 0)
    except (TypeError, ValueError):
        return 0
    return parsed if parsed > 0 else 0


def _region(raw: Any) -> dict[str, int] | None:
    if not isinstance(raw, Mapping):
        return None
    width = _positive_int(raw.get("width"))
    height = _positive_int(raw.get("height"))
    if width <= 0 or height <= 0:
        return None
    return {
        "x": int(raw.get("x") or 0),
        "y": int(raw.get("y") or 0),
        "width": width,
        "height": height,
    }


def _zero_origin(region: dict[str, int] | None) -> bool:
    return bool(region is not None and region["x"] == 0 and region["y"] == 0)


def _matching_fallback(
    fallback_meta: Mapping[str, Any] | None,
    source: str,
) -> Mapping[str, Any] | None:
    if not isinstance(fallback_meta, Mapping):
        return None
    fallback_source = str(
        fallback_meta.get("source") or fallback_meta.get("monitor_name") or ""
    ).strip()
    if source and fallback_source and fallback_source != source:
        return None
    return fallback_meta


def canonicalize_capture_meta(
    capture_meta: Mapping[str, Any] | None,
    *,
    source: str | None = None,
    fallback_meta: Mapping[str, Any] | None = None,
    monitor: Mapping[str, Any] | None = None,
    replace_zero_origin: bool = False,
    default_size: tuple[int, int] | None = None,
) -> dict[str, Any]:
    """Return normalized capture metadata using explicit, ordered fallbacks.

    Precedence is capture region → display bounds → caller-approved fallback
    metadata → monitor geometry.  The function performs no discovery or I/O,
    making the same input snapshots byte-for-byte deterministic.
    """
    out = dict(capture_meta or {})
    resolved_source = str(
        source or out.get("source") or out.get("monitor_name") or ""
    ).strip()
    if resolved_source:
        out.setdefault("source", resolved_source)
        out.setdefault("monitor_name", resolved_source)

    region = _region(out.get("region"))
    replaceable = region is None or (replace_zero_origin and _zero_origin(region))
    if replaceable:
        display_region = _region(out.get("display_bounds"))
        if display_region is not None:
            out["region"] = display_region
            region = display_region

    replaceable = region is None or (replace_zero_origin and _zero_origin(region))
    fallback = _matching_fallback(fallback_meta, resolved_source)
    if replaceable and fallback is not None:
        for key in _FALLBACK_META_KEYS:
            if fallback.get(key) is not None:
                out[key] = fallback[key]
        region = _region(out.get("region"))
        if region is None:
            region = _region(out.get("display_bounds"))
            if region is not None:
                out["region"] = region

    if region is None and isinstance(monitor, Mapping):
        region = _region(monitor)
        if region is not None:
            out["region"] = region

    if region is not None:
        out["region"] = region
    if isinstance(monitor, Mapping):
        out.setdefault("rotation", monitor.get("rotation") or "normal")

    default_width, default_height = default_size or (0, 0)
    width = _positive_int(out.get("width"))
    height = _positive_int(out.get("height"))
    if width <= 0:
        width = (region or {}).get("width", 0) or _positive_int(default_width)
    if height <= 0:
        height = (region or {}).get("height", 0) or _positive_int(default_height)
    if width > 0:
        out["width"] = width
    if height > 0:
        out["height"] = height
    return out


@dataclass(frozen=True)
class CaptureCoordinateMap:
    """Immutable ``vdisplay.coordinate-map.v1`` compiled from capture facts."""

    source: str
    capture_width: int
    capture_height: int
    region_x: int
    region_y: int
    region_width: int
    region_height: int
    rotation: str = "normal"
    mapping_source: str = "capture_local"

    @property
    def schema(self) -> str:
        return COORDINATE_MAP_V1

    @property
    def has_region(self) -> bool:
        return self.region_width > 0 and self.region_height > 0

    def region_dict(self) -> dict[str, int] | None:
        if not self.has_region:
            return None
        return {
            "x": self.region_x,
            "y": self.region_y,
            "width": self.region_width,
            "height": self.region_height,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "source": self.source,
            "coordinate_space": "capture_frame_local",
            "capture_width": self.capture_width,
            "capture_height": self.capture_height,
            "region": self.region_dict(),
            "rotation": self.rotation,
            "mapping_source": self.mapping_source,
        }

    def canonical_json(self) -> str:
        return json.dumps(
            self.canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )

    @property
    def coordinate_map_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {**self.canonical_dict(), "coordinate_map_hash": self.coordinate_map_hash}

    def global_to_local(
        self,
        global_x: int,
        global_y: int,
        *,
        clamp: bool = True,
    ) -> tuple[int, int] | None:
        if self.capture_width <= 0 or self.capture_height <= 0:
            return None
        if not self.has_region:
            local_x, local_y = int(global_x), int(global_y)
        else:
            right = self.region_x + self.region_width
            bottom = self.region_y + self.region_height
            if not clamp and not (
                self.region_x <= global_x < right
                and self.region_y <= global_y < bottom
            ):
                return None
            bounded_x = min(max(int(global_x), self.region_x), right - 1)
            bounded_y = min(max(int(global_y), self.region_y), bottom - 1)
            local_x, local_y = region_rel_to_local(
                bounded_x - self.region_x,
                bounded_y - self.region_y,
                png_w=self.capture_width,
                png_h=self.capture_height,
                region_w=self.region_width,
                region_h=self.region_height,
                rotation=self.rotation,
            )
        if 0 <= local_x < self.capture_width and 0 <= local_y < self.capture_height:
            return int(local_x), int(local_y)
        return None

    def clamp_global_rect(
        self,
        rect: tuple[int, int, int, int],
        *,
        min_width: int = 1,
        min_height: int = 1,
    ) -> tuple[int, int, int, int] | None:
        if not self.has_region:
            return None
        x, y, width, height = rect
        left = max(int(x), self.region_x)
        top = max(int(y), self.region_y)
        right = min(int(x + width), self.region_x + self.region_width)
        bottom = min(int(y + height), self.region_y + self.region_height)
        if right - left < min_width or bottom - top < min_height:
            return None
        return left, top, right - left, bottom - top

    def global_rect_to_local(
        self,
        rect: tuple[int, int, int, int],
        *,
        min_width: int = 1,
        min_height: int = 1,
    ) -> tuple[int, int, int, int] | None:
        left, top, width, height = rect
        top_left = self.global_to_local(left, top)
        bottom_right = self.global_to_local(left + width, top + height)
        if top_left is None or bottom_right is None:
            return None
        tlx, tly = top_left
        brx, bry = bottom_right
        local_left, local_right = sorted((tlx, brx))
        local_top, local_bottom = sorted((tly, bry))
        local_width = local_right - local_left
        local_height = local_bottom - local_top
        if local_width < min_width or local_height < min_height:
            return None
        if local_right > self.capture_width or local_bottom > self.capture_height:
            return None
        return local_left, local_top, local_width, local_height


def compile_capture_coordinate_map(
    capture_meta: Mapping[str, Any] | None,
    *,
    source: str | None = None,
    monitor: Mapping[str, Any] | None = None,
    display: str | None = None,
    default_size: tuple[int, int] = (2048, 1280),
) -> CaptureCoordinateMap:
    """Compile explicit capture facts into an immutable coordinate map."""
    meta = canonicalize_capture_meta(
        capture_meta,
        source=source,
        monitor=monitor,
        default_size=default_size,
    )
    resolved_source = str(
        source or meta.get("source") or meta.get("monitor_name") or ""
    ).strip()
    meta_source = str(meta.get("source") or meta.get("monitor_name") or "").strip()
    region = _region(meta.get("region"))
    mapping_source = "capture_region" if region is not None else "capture_local"
    if resolved_source and meta_source and resolved_source != meta_source:
        region = None

    resolved_monitor = monitor
    if region is None and resolved_monitor is None and resolved_source:
        try:
            from ..input.coords import monitor_by_name

            resolved_monitor = monitor_by_name(display or meta.get("display"), resolved_source)
        except Exception:
            resolved_monitor = None
    if region is None:
        region = _region(resolved_monitor)
        if region is not None:
            mapping_source = "monitor"

    width = _positive_int(meta.get("width")) or _positive_int(default_size[0])
    height = _positive_int(meta.get("height")) or _positive_int(default_size[1])
    rotation = str(
        meta.get("rotation")
        or (resolved_monitor or {}).get("rotation")
        or "normal"
    ).strip().lower()
    region = region or {"x": 0, "y": 0, "width": 0, "height": 0}
    return CaptureCoordinateMap(
        source=resolved_source,
        capture_width=width,
        capture_height=height,
        region_x=region["x"],
        region_y=region["y"],
        region_width=region["width"],
        region_height=region["height"],
        rotation=rotation,
        mapping_source=mapping_source,
    )


def coordinate_map_v1_schema() -> dict[str, Any]:
    resource = resources.files("vdisplay.data").joinpath(_SCHEMA_RESOURCE)
    return json.loads(resource.read_text(encoding="utf-8"))


__all__ = [
    "COORDINATE_MAP_V1",
    "CaptureCoordinateMap",
    "canonicalize_capture_meta",
    "compile_capture_coordinate_map",
    "coordinate_map_v1_schema",
]
