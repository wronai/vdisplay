"""Match portal ScreenCast PipeWire streams to xrandr monitors (multi-monitor Wayland)."""

from __future__ import annotations

from typing import Any

from .portal_screencast import _stream_properties_region


def session_has_multiple_streams(session: Any) -> bool:
    streams = list(getattr(session, "streams", None) or [])
    node_ids = list(getattr(session, "node_ids", None) or [])
    return len(streams) > 1 or len(node_ids) > 1


def _effective_monitor_aspect(monitor: dict[str, Any]) -> float:
    width = int(monitor.get("width") or 0)
    height = int(monitor.get("height") or 0)
    if height <= 0:
        return 1.0
    return width / height


def _stream_aspect(stream: dict[str, Any]) -> float:
    region = _stream_properties_region(stream.get("properties") or {})
    if region is None:
        return 1.0
    height = int(region.get("height") or 0)
    if height <= 0:
        return 1.0
    return int(region["width"]) / height


def _center_y(item: dict[str, Any], *, stream: bool) -> int:
    if stream:
        props = item.get("properties") or {}
        pos = props.get("position") or [0, 0]
        size = props.get("size") or [0, 0]
        return int(pos[1]) + int(size[1]) // 2
    return int(item.get("y") or 0) + int(item.get("height") or 0) // 2


def _is_portrait_aspect(aspect: float) -> bool:
    return aspect < 0.85


def _orientation_aspect(item: Any, *, stream: bool, streams: list[dict[str, Any]]) -> float:
    if stream:
        return _stream_aspect(streams[item])
    return _effective_monitor_aspect(item)


def _partition_by_orientation(
    items: list[Any],
    *,
    stream: bool,
    streams: list[dict[str, Any]],
) -> tuple[list[Any], list[Any]]:
    portrait = [item for item in items if _is_portrait_aspect(_orientation_aspect(item, stream=stream, streams=streams))]
    landscape = [item for item in items if not _is_portrait_aspect(_orientation_aspect(item, stream=stream, streams=streams))]
    return portrait, landscape


def _sorted_by_center_y(items: list[Any], *, stream: bool, streams: list[dict[str, Any]] | None = None) -> list[Any]:
    def _resolve(item: Any) -> Any:
        return streams[item] if stream and streams is not None and isinstance(item, int) else item
    return sorted(items, key=lambda item: _center_y(_resolve(item), stream=stream))


def _pair_orientation_group(
    monitors: list[dict[str, Any]],
    stream_indices: list[int],
    mapping: dict[str, int],
) -> None:
    for monitor, stream_idx in zip(monitors, stream_indices):
        name = str(monitor.get("name") or "")
        if name:
            mapping[name] = stream_idx


def _assign_remaining(
    monitors: list[dict[str, Any]],
    mapping: dict[str, int],
    streams: list[dict[str, Any]],
) -> None:
    used = set(mapping.values())
    remaining = [idx for idx in range(len(streams)) if idx not in used]
    for monitor in monitors:
        name = str(monitor.get("name") or "")
        if not name or name in mapping:
            continue
        mapping[name] = remaining.pop(0) if remaining else 0


def assign_screencast_streams_to_monitors(
    session: Any,
    monitors: list[dict[str, Any]],
) -> dict[str, int]:
    """One-to-one map: monitor name → PipeWire stream index."""
    streams = list(getattr(session, "streams", None) or [])
    if not streams or len(streams) == 1:
        return {str(item.get("name") or ""): 0 for item in monitors if item.get("name")}

    monitor_portrait, monitor_landscape = _partition_by_orientation(monitors, stream=False, streams=streams)
    stream_portrait, stream_landscape = _partition_by_orientation(
        list(range(len(streams))), stream=True, streams=streams
    )

    mapping: dict[str, int] = {}
    _pair_orientation_group(
        _sorted_by_center_y(monitor_portrait, stream=False),
        _sorted_by_center_y(stream_portrait, stream=True, streams=streams),
        mapping,
    )
    _pair_orientation_group(
        _sorted_by_center_y(monitor_landscape, stream=False),
        _sorted_by_center_y(stream_landscape, stream=True, streams=streams),
        mapping,
    )
    _assign_remaining(monitors, mapping, streams)
    return mapping


def screencast_stream_map(session: Any, monitors: list[dict[str, Any]]) -> dict[str, int]:
    names = tuple(sorted(str(item.get("name") or "") for item in monitors))
    cached = getattr(session, "_vdisplay_stream_map", None)
    if isinstance(cached, dict) and cached.get("names") == names:
        return dict(cached.get("map") or {})
    mapping = assign_screencast_streams_to_monitors(session, monitors)
    setattr(session, "_vdisplay_stream_map", {"names": names, "map": mapping})
    return mapping


def screencast_stream_index_for_monitor(
    session: Any,
    monitor: dict[str, Any],
    *,
    all_monitors: list[dict[str, Any]] | None = None,
) -> int:
    if not session_has_multiple_streams(session):
        return 0
    monitors = all_monitors if all_monitors is not None else [monitor]
    name = str(monitor.get("name") or "")
    if not name:
        return 0
    return screencast_stream_map(session, monitors).get(name, 0)
