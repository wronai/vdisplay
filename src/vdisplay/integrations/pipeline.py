"""Observe pipeline: capture metadata + IMGL + VQL in one reusable pass."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .imgl_bridge import attach_imgl_to_context, imgl_enabled
from .observe_cache import (
    evaluate_map_drift,
    load_cached_context,
    map_drift_blocks_cache,
    merge_cached_analysis,
    observe_cache_enabled,
    store_context_cache,
)
from .screen_context import ScreenContext, load_environment_snapshot, screen_context_from_capture
from .vql_bridge import vql_enabled, write_vql_artifacts


def _observe_flag() -> bool | None:
    flag = os.environ.get("VDISPLAY_OBSERVE", "").strip().lower()
    if flag in {"1", "true", "yes", "on"}:
        return True
    if flag in {"0", "false", "no", "off"}:
        return False
    return None


def observe_enabled() -> bool:
    explicit = _observe_flag()
    if explicit is not None:
        return explicit
    from .imgl_bridge import imgl_available
    from .vql_bridge import vql_available
    return imgl_available() or vql_available()


def _evaluate_drift_with_png(ctx: ScreenContext, path: Path) -> None:
    png_bytes: bytes | None = None
    if path.is_file() and ctx.map_pack:
        try:
            png_bytes = path.read_bytes()
        except OSError:
            png_bytes = None
    if ctx.map_pack:
        evaluate_map_drift(ctx, png_bytes)


def _resolve_cached_or_imgl(ctx: ScreenContext, *, include_imgl: bool) -> ScreenContext | None:
    cached: ScreenContext | None = None
    if observe_cache_enabled() and ctx.fingerprint:
        cached = load_cached_context(ctx.fingerprint)
    if cached and not map_drift_blocks_cache(ctx):
        merge_cached_analysis(ctx, cached)
    elif include_imgl and imgl_enabled():
        attach_imgl_to_context(ctx)
    return cached


def _maybe_write_vql(
    ctx: ScreenContext,
    path: Path,
    *,
    include_vql: bool,
    cached: ScreenContext | None,
    vql_path: str | Path | None,
    svg_path: str | Path | None,
) -> None:
    if include_vql and vql_enabled() and path.is_file():
        if not (cached and ctx.vql.get("program")):
            write_vql_artifacts(ctx, vql_path=vql_path, svg_path=svg_path)


def _persist_observe_sidecar(ctx: ScreenContext, *, write_sidecar: bool) -> None:
    if write_sidecar:
        ctx.write_sidecar()
    store_context_cache(ctx)


def observe_screen(
    *,
    image_path: str | Path,
    capture_meta: dict[str, Any] | None = None,
    diagnostics: dict[str, Any] | None = None,
    map_path: str | Path | None = None,
    display: str | None = None,
    include_imgl: bool = True,
    include_vql: bool = True,
    write_sidecar: bool = True,
    vql_path: str | Path | None = None,
    svg_path: str | Path | None = None,
) -> ScreenContext:
    path = Path(image_path).expanduser()
    payload = dict(capture_meta or {})
    payload.setdefault("path", str(path))
    ctx = screen_context_from_capture(
        payload,
        image_path=str(path),
        diagnostics=diagnostics,
        map_path=str(map_path) if map_path else None,
    )
    ctx.environment.update(load_environment_snapshot(display=display or payload.get("display")))
    _evaluate_drift_with_png(ctx, path)
    cached = _resolve_cached_or_imgl(ctx, include_imgl=include_imgl)

    if not ctx.nl and payload.get("nl"):
        ctx.nl = str(payload["nl"])

    _maybe_write_vql(ctx, path, include_vql=include_vql, cached=cached, vql_path=vql_path, svg_path=svg_path)
    _persist_observe_sidecar(ctx, write_sidecar=write_sidecar)
    return ctx


def _build_enriched_payload(ctx: ScreenContext, payload: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(payload)
    enriched["screen_context"] = {
        "fingerprint": ctx.fingerprint,
        "artifacts": ctx.artifacts,
        "nl": ctx.nl,
    }
    sidecar = ctx.artifacts.get("context") or str(ctx.sidecar_path())
    if sidecar:
        enriched["screen_context"]["path"] = sidecar
        enriched["screen_context_path"] = sidecar
    if ctx.verify.get("map_drift"):
        enriched["screen_context"]["map_drift"] = ctx.verify["map_drift"]
    if ctx.imgl.get("cache_hit"):
        enriched["screen_context"]["cache_hit"] = True
    if ctx.vql.get("program"):
        vql_block: dict[str, Any] = {"path": ctx.artifacts.get("vql"), "reverse": ctx.vql.get("reverse")}
        if ctx.vql.get("capture_validation"):
            vql_block["capture_validation"] = ctx.vql["capture_validation"]
        enriched["vql"] = vql_block
    if ctx.vql.get("capture_validation"):
        enriched["capture_validation"] = ctx.vql["capture_validation"]
    if ctx.imgl.get("ok"):
        enriched["imgl"] = {
            "ok": True,
            "element_count": ctx.imgl.get("element_count"),
            "window_count": ctx.imgl.get("window_count"),
        }
    if ctx.nl and not enriched.get("nl"):
        enriched["nl"] = ctx.nl
    return enriched


def _env_bool(key: str, default: str = "1") -> bool:
    return os.environ.get(key, default).strip().lower() not in {"0", "false", "no"}


def enrich_capture_payload(
    payload: dict[str, Any],
    *,
    diagnostics: dict[str, Any] | None = None,
    map_path: str | None = None,
) -> dict[str, Any]:
    """Attach ScreenContext sidecar fields to a capture/result payload."""
    if not observe_enabled():
        return payload

    image_path = payload.get("path") or payload.get("saved")
    if not image_path or not Path(str(image_path)).is_file():
        return payload

    ctx = observe_screen(
        image_path=str(image_path),
        capture_meta=payload,
        diagnostics=diagnostics,
        map_path=map_path,
        include_vql=_env_bool("VDISPLAY_OBSERVE_VQL"),
        write_sidecar=_env_bool("VDISPLAY_OBSERVE_SIDECAR"),
    )
    return _build_enriched_payload(ctx, payload)
