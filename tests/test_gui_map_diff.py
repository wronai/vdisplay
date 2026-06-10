"""PR-27 — GUI map drift detection and refresh."""

from __future__ import annotations

from pathlib import Path

import pytest

from vdisplay.control.gui_map import (
    GuiMapBounds,
    GuiMapPack,
    GuiMapRegion,
    element_from_ocr_box,
    save_gui_map,
)
from vdisplay.control.gui_map_diff import diff_gui_map, match_ocr_box_for_element, refresh_gui_map
from vdisplay.control.models import ControlBounds
from vdisplay.control.vision_ocr import OcrTextBox


def _fake_png() -> bytes:
    from PIL import Image
    import io

    image = Image.new("RGB", (400, 200), color=(240, 240, 240))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def _sample_pack(png: bytes) -> GuiMapPack:
    box = OcrTextBox("Ask anything", ControlBounds(x=10, y=20, width=120, height=18), 0.91)
    element = element_from_ocr_box(
        box,
        element_id="ask_anything",
        region_id="chat",
        capture_meta={"width": 400, "height": 200},
        monitor="DP-2",
        rotation="left",
        png=png,
    )
    return GuiMapPack(
        monitor="DP-2",
        rotation="left",
        capture_meta={"width": 400, "height": 200},
        elements={"ask_anything": element},
        regions={
            "chat": GuiMapRegion(
                id="chat",
                label="chat",
                scope_bounds=GuiMapBounds(x=0, y=0, width=400, height=200),
                elements=["ask_anything"],
                fingerprint=element.tile_fingerprint,
            )
        },
    )


def test_match_ocr_box_for_element_prefers_label_and_nearest() -> None:
    element = _sample_pack(_fake_png()).elements["ask_anything"]
    boxes = [
        OcrTextBox("Cancel", ControlBounds(x=200, y=20, width=60, height=18), 0.95),
        OcrTextBox("Ask anything", ControlBounds(x=12, y=22, width=118, height=18), 0.92),
    ]
    matched = match_ocr_box_for_element(element, boxes)
    assert matched is not None
    assert matched.text == "Ask anything"


def test_diff_gui_map_ok_when_stable(monkeypatch: pytest.MonkeyPatch) -> None:
    png = _fake_png()
    pack = _sample_pack(png)
    boxes = [OcrTextBox("Ask anything", ControlBounds(x=10, y=20, width=120, height=18), 0.91)]
    monkeypatch.setattr("vdisplay.control.vision_ocr.ocr_png", lambda _png: boxes)
    diff = diff_gui_map(pack, png, {"width": 400, "height": 200})
    assert diff.ok is True
    assert diff.summary["ok"] == 1
    assert diff.elements[0].status == "ok"


def test_diff_gui_map_detects_bounds_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    png = _fake_png()
    pack = _sample_pack(png)
    boxes = [OcrTextBox("Ask anything", ControlBounds(x=80, y=90, width=120, height=18), 0.91)]
    monkeypatch.setattr("vdisplay.control.vision_ocr.ocr_png", lambda _png: boxes)
    diff = diff_gui_map(pack, png, {"width": 400, "height": 200})
    assert diff.drifted is True
    assert diff.elements[0].status == "bounds"


def test_diff_gui_map_detects_missing_anchor(monkeypatch: pytest.MonkeyPatch) -> None:
    png = _fake_png()
    pack = _sample_pack(png)
    monkeypatch.setattr("vdisplay.control.vision_ocr.ocr_png", lambda _png: [])
    diff = diff_gui_map(pack, png, {"width": 400, "height": 200})
    assert diff.drifted is True
    assert diff.elements[0].status == "missing"


def test_refresh_gui_map_updates_bounds(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    png = _fake_png()
    pack = _sample_pack(png)
    moved = [OcrTextBox("Ask anything", ControlBounds(x=15, y=24, width=120, height=18), 0.93)]
    monkeypatch.setattr("vdisplay.control.vision_ocr.ocr_png", lambda _png: moved)
    updated, diff = refresh_gui_map(pack, png, {"width": 400, "height": 200})
    assert updated.elements["ask_anything"].raw_bounds.x == 15
    assert updated.elements["ask_anything"].click_point.x == updated.elements["ask_anything"].action_bounds.center[0]
    path = tmp_path / "map.json"
    save_gui_map(path, updated)
    assert path.exists()


def test_map_diff_service(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.application.services.map import map_diff

    png = _fake_png()
    pack = _sample_pack(png)
    path = tmp_path / "map.json"
    save_gui_map(path, pack)
    monkeypatch.setattr(
        "vdisplay.application.services.map._capture",
        lambda **_k: (png, {"width": 400, "height": 200}),
    )
    monkeypatch.setattr(
        "vdisplay.control.vision_ocr.ocr_png",
        lambda _png: [OcrTextBox("Ask anything", ControlBounds(x=10, y=20, width=120, height=18), 0.91)],
    )
    payload = map_diff(map_path=str(path))
    assert payload["ok"] is True
    assert payload["summary"]["ok"] == 1
