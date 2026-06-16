"""GUI Map Pack build/diff/refresh use-cases (PR-26/27)."""

from __future__ import annotations

from typing import Any

from ...control.gui_map import build_gui_map_from_ocr, load_gui_map
from ...control.gui_map_diff import diff_gui_map, refresh_gui_map
from ...control.gui_map_export import write_map_artifacts
from ...control.screenshot_verify import enrich_screencast_stream_meta
from ...exceptions import VDisplayError


def _prepare_capture_meta(
    *,
    display: str | None,
    monitor: str | None,
    png: bytes,
    meta: dict[str, Any],
) -> tuple[dict[str, Any], str | None, str | None]:
    meta = enrich_screencast_stream_meta(dict(meta))
    rotation = None
    if monitor:
        meta["source"] = monitor
        meta["monitor"] = monitor
        rotation = _monitor_rotation(display, monitor)
        meta["rotation"] = rotation
    elif meta.get("source"):
        monitor = str(meta["source"])
        rotation = _monitor_rotation(display, monitor)
        meta["rotation"] = rotation
    try:
        from PIL import Image
        import io

        with Image.open(io.BytesIO(png)) as image:
            meta.setdefault("width", image.width)
            meta.setdefault("height", image.height)
    except Exception:
        pass
    return meta, monitor, rotation


def map_build(
    *,
    display: str | None = None,
    output: str,
    md: str | None = None,
    svg: str | None = None,
    monitor: str | None = None,
    region_id: str = "screen",
    region_label: str | None = None,
    min_confidence: float = 0.4,
    crop_bounds: str | None = None,
    min_text_len: int = 2,
    capture_fn: Any | None = None,
) -> dict[str, Any]:
    """Capture screen, OCR text boxes (optionally scoped), emit map.json (+ optional md/svg)."""
    from ...control.gui_map import parse_crop_bounds

    png, meta = _capture(display=display, monitor=monitor, capture_fn=capture_fn)
    meta, monitor, rotation = _prepare_capture_meta(display=display, monitor=monitor, png=png, meta=meta)
    scope_bounds = parse_crop_bounds(crop_bounds) if crop_bounds else None

    pack = build_gui_map_from_ocr(
        png,
        meta,
        monitor=monitor,
        rotation=rotation,
        region_id=region_id,
        region_label=region_label or region_id,
        min_confidence=min_confidence,
        scope_bounds=scope_bounds,
        min_text_len=min_text_len,
    )
    written = write_map_artifacts(
        pack,
        json_path=output,
        md_path=md,
        svg_path=svg,
        png=png if svg else None,
        title=f"{monitor or 'screen'} / {region_id}",
    )
    try:
        from ..gui_map_events import record_gui_map_built

        record_gui_map_built(
            map_path=output,
            element_count=len(pack.elements),
            region_count=len(pack.regions),
            map_id=region_id,
            scope_ids=list(pack.regions.keys()),
        )
    except Exception:
        pass
    return {
        "ok": True,
        "elements": len(pack.elements),
        "regions": len(pack.regions),
        "monitor": monitor,
        "rotation": rotation,
        "scope_bounds": pack.regions.get(region_id).scope_bounds.to_dict() if region_id in pack.regions else None,
        "artifacts": written,
    }


def map_show(*, map_path: str) -> dict[str, Any]:
    pack = load_gui_map(map_path)
    return {
        "ok": True,
        "map": map_path,
        "monitor": pack.monitor,
        "rotation": pack.rotation,
        "regions": {key: region.to_dict() for key, region in pack.regions.items()},
        "elements": {key: element.to_dict() for key, element in pack.elements.items()},
    }


def map_diff(
    *,
    map_path: str,
    display: str | None = None,
    monitor: str | None = None,
    scope: str | None = None,
    min_confidence: float = 0.4,
    capture_fn: Any | None = None,
) -> dict[str, Any]:
    pack = load_gui_map(map_path)
    png, meta = _capture(display=display, monitor=monitor or pack.monitor, capture_fn=capture_fn)
    meta, _, _ = _prepare_capture_meta(
        display=display,
        monitor=monitor or pack.monitor,
        png=png,
        meta=meta,
    )
    diff = diff_gui_map(
        pack,
        png,
        meta,
        scope_id=scope,
        min_confidence=min_confidence,
    )
    payload = {"ok": diff.ok, "map": map_path, "scope": scope, **diff.to_dict()}
    if diff.drifted:
        try:
            from ..gui_map_events import record_gui_map_drift

            record_gui_map_drift(map_path=map_path, drift=diff.to_dict(), scope_id=scope)
        except Exception:
            pass
    return payload


def map_refresh(
    *,
    map_path: str,
    output: str | None = None,
    display: str | None = None,
    monitor: str | None = None,
    scope: str | None = None,
    min_confidence: float = 0.4,
    add_new: bool = False,
    force: bool = False,
    md: str | None = None,
    svg: str | None = None,
    capture_fn: Any | None = None,
) -> dict[str, Any]:
    pack = load_gui_map(map_path)
    png, meta = _capture(display=display, monitor=monitor or pack.monitor, capture_fn=capture_fn)
    meta, monitor_name, rotation = _prepare_capture_meta(
        display=display,
        monitor=monitor or pack.monitor,
        png=png,
        meta=meta,
    )
    updated, diff = refresh_gui_map(
        pack,
        png,
        meta,
        scope_id=scope,
        min_confidence=min_confidence,
        add_new=add_new,
    )
    if monitor_name:
        updated.monitor = monitor_name
    if rotation:
        updated.rotation = rotation
    updated.capture_meta = dict(meta)
    out_path = output or map_path
    write_skipped = bool(diff.recommendation == "refresh_required" and not force)
    if write_skipped:
        written = {}
    else:
        written = write_map_artifacts(
            updated,
            json_path=out_path,
            md_path=md,
            svg_path=svg,
            png=png if svg else None,
            title=f"{monitor_name or updated.monitor or 'screen'} / refresh",
        )
    if diff.drifted:
        try:
            from ..gui_map_events import record_gui_map_drift

            record_gui_map_drift(map_path=map_path, drift=diff.to_dict(), scope_id=scope)
        except Exception:
            pass
    if not write_skipped:
        try:
            from ..gui_map_events import record_gui_map_built

            record_gui_map_built(
                map_path=out_path,
                element_count=len(updated.elements),
                region_count=len(updated.regions),
                scope_ids=list(updated.regions.keys()),
            )
        except Exception:
            pass
    payload = {
        "ok": diff.ok,
        "drifted": diff.drifted,
        "map": map_path,
        "output": out_path,
        "scope": scope,
        "summary": diff.summary,
        "diff": diff.to_dict(),
        "artifacts": written,
    }
    if write_skipped:
        payload["write_skipped"] = True
        payload["hint"] = (
            "map refresh detected refresh_required and did not overwrite the map. "
            "Rebuild/recalibrate the map for this screen, or rerun with --force for manual debugging."
        )
    return payload


def _capture(
    *,
    display: str | None,
    monitor: str | None = None,
    capture_fn: Any | None = None,
) -> tuple[bytes, dict[str, Any]]:
    if capture_fn is not None:
        png = capture_fn(display=display)
        return png, {"method": "injected"}

    agent_capture = _capture_via_agent(display=display, monitor=monitor)
    if agent_capture is not None:
        return agent_capture

    from ...capture.host import capture_host_png
    from ...agent_config import resolve_agent_url

    if resolve_agent_url(allow_auto=True):
        raise VDisplayError(
            "map capture failed via agent. Ensure screencast is ready:\n"
            "  1. vdisplay-agent serve\n"
            "  2. vdisplay agent screencast start\n"
            "(screencast is lost every time the agent restarts)"
        )

    monitor_index = _monitor_index(display, monitor)
    try:
        return capture_host_png(
            display=display,
            monitor=monitor_index,
            source=monitor or "primary",
        )
    except VDisplayError:
        raise
    except Exception as exc:
        raise VDisplayError(f"map capture failed: {exc}") from exc


def _capture_via_agent(
    *,
    display: str | None,
    monitor: str | None,
) -> tuple[bytes, dict[str, Any]] | None:
    """Use agent ScreenCast when the CLI has no in-process portal session."""
    from pathlib import Path
    import tempfile

    from ...agent_config import resolve_agent_url
    from ...client import AgentClient

    agent_url = resolve_agent_url(allow_auto=True)
    if not agent_url:
        return None

    client = AgentClient(agent_url)
    status = client.screencast_status()
    if not status.get("ready"):
        raise VDisplayError(
            "agent screencast not ready. Start in order:\n"
            "  1. vdisplay-agent serve\n"
            "  2. vdisplay agent screencast start\n"
            "(screencast is lost when the agent restarts — run step 2 again after serve)"
        )

    kwargs: dict[str, Any] = {"display": display}
    if monitor:
        kwargs["source"] = monitor
    with tempfile.TemporaryDirectory(prefix="vdisplay-map-") as tmpdir:
        png, meta = client.capture_png_bytes(output=str(Path(tmpdir) / "frame.png"), **kwargs)
    return png, enrich_screencast_stream_meta(dict(meta))


def _monitor_index(display: str | None, monitor: str | None) -> int:
    if not monitor:
        return 1
    from ...discovery import list_monitors, resolve_host_display

    resolved = resolve_host_display(display)
    for index, item in enumerate(list_monitors(resolved), start=1):
        if str(item.get("name") or "") == monitor:
            return index
    return 1


def _monitor_rotation(display: str | None, monitor: str) -> str | None:
    from ...discovery import list_monitors, resolve_host_display

    resolved = resolve_host_display(display)
    for item in list_monitors(resolved):
        if str(item.get("name") or "") == monitor:
            return str(item.get("rotation") or "normal")
    return None
