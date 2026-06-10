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
    min_confidence: float = 0.5,
    capture_fn: Any | None = None,
) -> dict[str, Any]:
    """Capture screen, OCR all text boxes, emit map.json (+ optional md/svg)."""
    png, meta = _capture(display=display, capture_fn=capture_fn)
    meta, monitor, rotation = _prepare_capture_meta(display=display, monitor=monitor, png=png, meta=meta)

    pack = build_gui_map_from_ocr(
        png,
        meta,
        monitor=monitor,
        rotation=rotation,
        region_id=region_id,
        region_label=region_label or region_id,
        min_confidence=min_confidence,
    )
    written = write_map_artifacts(
        pack,
        json_path=output,
        md_path=md,
        svg_path=svg,
        png=png if svg else None,
        title=f"{monitor or 'screen'} / {region_id}",
    )
    return {
        "ok": True,
        "elements": len(pack.elements),
        "regions": len(pack.regions),
        "monitor": monitor,
        "rotation": rotation,
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
    min_confidence: float = 0.5,
    capture_fn: Any | None = None,
) -> dict[str, Any]:
    pack = load_gui_map(map_path)
    png, meta = _capture(display=display, capture_fn=capture_fn)
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
    return {"ok": diff.ok, "map": map_path, "scope": scope, **diff.to_dict()}


def map_refresh(
    *,
    map_path: str,
    output: str | None = None,
    display: str | None = None,
    monitor: str | None = None,
    scope: str | None = None,
    min_confidence: float = 0.5,
    add_new: bool = False,
    md: str | None = None,
    svg: str | None = None,
    capture_fn: Any | None = None,
) -> dict[str, Any]:
    pack = load_gui_map(map_path)
    png, meta = _capture(display=display, capture_fn=capture_fn)
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
    out_path = output or map_path
    written = write_map_artifacts(
        updated,
        json_path=out_path,
        md_path=md,
        svg_path=svg,
        png=png if svg else None,
        title=f"{monitor_name or updated.monitor or 'screen'} / refresh",
    )
    return {
        "ok": diff.ok,
        "drifted": diff.drifted,
        "map": map_path,
        "output": out_path,
        "scope": scope,
        "summary": diff.summary,
        "diff": diff.to_dict(),
        "artifacts": written,
    }


def _capture(*, display: str | None, capture_fn: Any | None) -> tuple[bytes, dict[str, Any]]:
    if capture_fn is not None:
        png = capture_fn(display=display)
        return png, {"method": "injected"}
    from ...capture.host import capture_host_png

    try:
        return capture_host_png(display=display)
    except VDisplayError:
        raise
    except Exception as exc:
        raise VDisplayError(f"map build capture failed: {exc}") from exc


def _monitor_rotation(display: str | None, monitor: str) -> str | None:
    from ...discovery import list_monitors, resolve_host_display

    resolved = resolve_host_display(display)
    for item in list_monitors(resolved):
        if str(item.get("name") or "") == monitor:
            return str(item.get("rotation") or "normal")
    return None
