"""Incremental observe cache — reuse ScreenContext / OCR by fingerprint."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .screen_context import ScreenContext


def observe_cache_enabled() -> bool:
    flag = os.environ.get("VDISPLAY_OBSERVE_CACHE", "1").strip().lower()
    return flag not in {"0", "false", "no", "off"}


def session_artifacts_root() -> Path | None:
    explicit = os.environ.get("VDISPLAY_SESSION_DIR", "").strip()
    if explicit:
        return Path(explicit).expanduser()
    try:
        from ..application.session_recorder import _current_recorder

        current = _current_recorder.get()
        if current is not None:
            return current.session_dir
    except Exception:
        pass
    if os.environ.get("VDISPLAY_SESSION", "").strip().lower() not in {"1", "true", "yes"}:
        return None
    base = Path(os.environ.get("VDISPLAY_SESSION_BASE", ".vdisplay")).expanduser()
    if not base.is_dir():
        return None
    sessions = sorted(base.glob("*__*"), key=lambda item: item.stat().st_mtime, reverse=True)
    return sessions[0] if sessions else None


def cache_dir(session_root: Path | None = None) -> Path | None:
    root = session_root or session_artifacts_root()
    if root is None:
        return None
    return root / "artifacts" / "observe"


def vql_cache_dir(session_root: Path | None = None) -> Path | None:
    root = session_root or session_artifacts_root()
    if root is None:
        return None
    return root / "artifacts" / "vql"


def _cache_path(fingerprint: str, session_root: Path | None = None) -> Path | None:
    base = cache_dir(session_root)
    if base is None or not fingerprint:
        return None
    return base / f"{fingerprint}.context.json"


def load_cached_context(
    fingerprint: str,
    *,
    session_root: Path | None = None,
) -> ScreenContext | None:
    if not observe_cache_enabled() or not fingerprint:
        return None
    path = _cache_path(fingerprint, session_root)
    if path is None or not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return ScreenContext.from_dict(payload)
    except Exception:
        return None


def store_context_cache(
    ctx: ScreenContext,
    *,
    session_root: Path | None = None,
) -> Path | None:
    if not observe_cache_enabled() or not ctx.fingerprint:
        return None
    base = cache_dir(session_root)
    if base is None:
        return None
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{ctx.fingerprint}.context.json"
    path.write_text(json.dumps(ctx.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    ctx.artifacts.setdefault("observe_cache", str(path.resolve()))

    vql_base = vql_cache_dir(session_root)
    if vql_base and ctx.vql.get("program"):
        vql_base.mkdir(parents=True, exist_ok=True)
        vql_path = vql_base / f"{ctx.fingerprint}.vql.json"
        vql_path.write_text(json.dumps(ctx.vql["program"], indent=2, ensure_ascii=False), encoding="utf-8")
        ctx.artifacts.setdefault("vql_cache", str(vql_path.resolve()))

    return path


def merge_cached_analysis(ctx: ScreenContext, cached: ScreenContext) -> ScreenContext:
    """Reuse IMGL/VQL blocks when fingerprint matches and map drift is absent."""
    if cached.imgl.get("ok"):
        ctx.imgl = dict(cached.imgl)
        ctx.imgl["cache_hit"] = True
    if cached.vql.get("program"):
        ctx.vql = dict(cached.vql)
        ctx.vql["cache_hit"] = True
    if cached.nl and not ctx.nl:
        ctx.nl = cached.nl
    for key, value in cached.artifacts.items():
        ctx.artifacts.setdefault(key, value)
    return ctx


def _drift_summary_recommends_refresh(summary: dict[str, Any], recommendation: str) -> bool:
    missing = int(summary.get("missing") or 0)
    bounds = int(summary.get("bounds") or 0)
    if missing > 0 or bounds > 0:
        return recommendation != "stable_with_cosmetic_drift"
    return False


def _drift_status_recommends_refresh(status: str) -> bool:
    return status in {"refresh_required", "drift", "bounds", "missing", "fingerprint"}


def _drift_recommends_refresh(drift: dict[str, Any]) -> bool:
    recommendation = str(drift.get("recommendation") or "").lower()
    if recommendation == "refresh_required":
        return True
    if drift.get("drifted") is True and drift.get("actionable") is True:
        return True
    status = str(drift.get("status") or drift.get("summary") or "").lower()
    if _drift_status_recommends_refresh(status):
        return True
    summary = drift.get("summary")
    if isinstance(summary, dict):
        if _drift_summary_recommends_refresh(summary, recommendation):
            return True
    if int(drift.get("missing") or drift.get("missing_count") or 0) > 0:
        return True
    return False


def map_drift_blocks_cache(ctx: ScreenContext) -> bool:
    """Return True when GUI map drift suggests skipping cached OCR/analysis."""
    if not ctx.map_pack:
        return False
    verify = ctx.verify or {}
    drift = verify.get("map_drift") or verify.get("gui_map_drift")
    if not isinstance(drift, dict):
        return False
    return _drift_recommends_refresh(drift)


def evaluate_map_drift(
    ctx: ScreenContext,
    png: bytes | None = None,
) -> dict[str, Any] | None:
    """Compare attached GUI map against live screenshot OCR."""
    if not ctx.map_pack:
        return None

    image_bytes = png
    if image_bytes is None:
        path = Path(ctx.image_path).expanduser()
        if not path.is_file():
            return None
        try:
            image_bytes = path.read_bytes()
        except OSError as exc:
            ctx.verify["map_drift"] = {"ok": False, "error": str(exc)}
            return ctx.verify["map_drift"]

    try:
        from ..control.gui_map import GuiMapPack
        from ..control.gui_map_diff import assess_map_drift, diff_gui_map

        pack = GuiMapPack.from_dict(ctx.map_pack)
        capture_meta = dict(ctx.capture)
        diff = diff_gui_map(pack, image_bytes, capture_meta)
        recommendation, actionable, key_targets = assess_map_drift(diff)
        drift_payload: dict[str, Any] = {
            "ok": diff.ok,
            "drifted": diff.drifted,
            "summary": diff.summary,
            "recommendation": recommendation,
            "actionable": actionable,
            "key_targets": key_targets,
        }
        ctx.verify["map_drift"] = drift_payload
        return drift_payload
    except Exception as exc:
        ctx.verify["map_drift"] = {"ok": False, "error": str(exc)}
        return ctx.verify["map_drift"]


def _item_to_ocr_box(item: dict[str, Any]) -> "OcrTextBox":
    from ..control.models import ControlBounds
    from ..control.vision_ocr import OcrTextBox

    bbox = item.get("bbox") or {}
    x = int(bbox.get("x") or 0)
    y = int(bbox.get("y") or 0)
    w = int(bbox.get("w") or bbox.get("width") or 0)
    h = int(bbox.get("h") or bbox.get("height") or 0)
    return OcrTextBox(
        text=str(item.get("text") or ""),
        bounds=ControlBounds(x=x, y=y, width=w, height=h),
        confidence=float(item.get("confidence") or 0.0),
    )


def ocr_boxes_from_cached_context(ctx: ScreenContext) -> list[Any] | None:
    """Return OCR boxes from cached IMGL scene when available."""
    if not ctx.imgl.get("ok"):
        return None
    scene = ctx.imgl.get("scene") or {}
    ocr_boxes = scene.get("ocr_boxes") or []
    if not ocr_boxes:
        return None
    return [_item_to_ocr_box(item) for item in ocr_boxes] or None
