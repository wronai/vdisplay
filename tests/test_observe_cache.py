"""Observe cache tests (Etap 4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vdisplay.control.vision_ocr import ocr_png
from vdisplay.integrations.observe_cache import (
    load_cached_context,
    map_drift_blocks_cache,
    merge_cached_analysis,
    store_context_cache,
)
from vdisplay.integrations.pipeline import observe_screen
from vdisplay.integrations.screen_context import ScreenContext


def test_store_and_load_cached_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_SESSION_DIR", str(tmp_path))
    ctx = ScreenContext(
        image_path=str(tmp_path / "screen.png"),
        fingerprint="abc123deadbeef",
        nl="Cached screen.",
        imgl={"ok": True, "scene": {"ocr_boxes": [{"text": "OK", "bbox": {"x": 1, "y": 2, "w": 3, "h": 4}, "confidence": 90.0}]}},
        vql={"program": {"version": "1.0", "metadata": {}}},
    )
    stored = store_context_cache(ctx)
    assert stored is not None
    assert stored.is_file()
    loaded = load_cached_context("abc123deadbeef", session_root=tmp_path)
    assert loaded is not None
    assert loaded.nl == "Cached screen."
    assert loaded.imgl.get("ok") is True


def test_merge_cached_analysis_skips_imgl_rerun() -> None:
    live = ScreenContext(fingerprint="fp1", nl="")
    cached = ScreenContext(
        fingerprint="fp1",
        nl="From cache",
        imgl={"ok": True, "scene": {"elements": []}},
        vql={"program": {"version": "1.0"}},
    )
    merge_cached_analysis(live, cached)
    assert live.imgl.get("cache_hit") is True
    assert live.vql.get("cache_hit") is True
    assert live.nl == "From cache"


def test_map_drift_blocks_cache_on_refresh_required() -> None:
    ctx = ScreenContext(
        map_pack={"elements": {}, "regions": {}},
        verify={
            "map_drift": {
                "recommendation": "refresh_required",
                "drifted": True,
                "actionable": True,
                "summary": {"missing": 2, "bounds": 0},
            }
        },
    )
    assert map_drift_blocks_cache(ctx) is True


def test_map_drift_allows_cosmetic_drift() -> None:
    ctx = ScreenContext(
        map_pack={"elements": {}, "regions": {}},
        verify={
            "map_drift": {
                "recommendation": "stable_with_cosmetic_drift",
                "drifted": False,
                "summary": {"fingerprint": 1, "missing": 0, "bounds": 0},
            }
        },
    )
    assert map_drift_blocks_cache(ctx) is False


def test_observe_screen_uses_cache_on_second_pass(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VDISPLAY_SESSION_DIR", str(tmp_path))
    monkeypatch.setenv("VDISPLAY_IMGL", "0")
    monkeypatch.setenv("VDISPLAY_VQL", "0")
    png = tmp_path / "screen.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
    meta = {"path": str(png), "width": 10, "height": 10, "source": "test"}

    first = observe_screen(
        image_path=png,
        capture_meta=meta,
        include_imgl=False,
        include_vql=False,
        write_sidecar=False,
    )
    first.imgl = {"ok": True, "scene": {"ocr_boxes": []}, "source": "test"}
    store_context_cache(first)

    second = observe_screen(
        image_path=png,
        capture_meta=meta,
        include_imgl=False,
        include_vql=False,
        write_sidecar=False,
    )
    assert second.imgl.get("cache_hit") is True


def test_ocr_png_reads_cached_sidecar(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sidecar = tmp_path / "screen.png.context.json"
    sidecar.write_text(
        json.dumps(
            {
                "image_path": str(tmp_path / "screen.png"),
                "fingerprint": "fp",
                "imgl": {
                    "ok": True,
                    "scene": {
                        "ocr_boxes": [
                            {"text": "JetBrains", "bbox": {"x": 0, "y": 0, "w": 10, "h": 10}, "confidence": 95.0}
                        ]
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("VDISPLAY_SCREEN_CONTEXT_PATH", str(sidecar))
    monkeypatch.setenv("VDISPLAY_VISION_BACKEND", "local")
    boxes = ocr_png(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)
    assert len(boxes) == 1
    assert boxes[0].text == "JetBrains"
