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
from vdisplay.control.gui_map_diff import assess_map_drift, diff_gui_map, match_ocr_box_for_element, refresh_gui_map
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


def test_map_refresh_skips_write_when_refresh_required(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.application.services.map import map_refresh

    png = _fake_png()
    pack = _sample_pack(png)
    pack.capture_meta = {"source": "DP-2", "rotation": "left"}
    path = tmp_path / "map.json"
    save_gui_map(path, pack)
    before = path.read_text(encoding="utf-8")
    monkeypatch.setattr(
        "vdisplay.application.services.map._capture",
        lambda **_k: (png, {"source": "HDMI-1", "rotation": "normal", "width": 400, "height": 200}),
    )
    monkeypatch.setattr("vdisplay.control.vision_ocr.ocr_png", lambda _png: [])

    payload = map_refresh(map_path=str(path), monitor="HDMI-1")

    assert payload["ok"] is False
    assert payload["write_skipped"] is True
    assert payload["diff"]["recommendation"] == "refresh_required"
    assert payload["artifacts"] == {}
    assert path.read_text(encoding="utf-8") == before


def test_map_refresh_updates_monitor_contract_with_force(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.application.services.map import map_refresh
    from vdisplay.control.gui_map import load_gui_map

    png = _fake_png()
    pack = _sample_pack(png)
    pack.monitor = "DP-2"
    pack.rotation = "left"
    pack.capture_meta = {"source": "DP-2", "rotation": "left"}
    path = tmp_path / "map.json"
    save_gui_map(path, pack)
    monkeypatch.setattr(
        "vdisplay.application.services.map._capture",
        lambda **_k: (png, {"source": "HDMI-1", "rotation": "normal", "width": 400, "height": 200}),
    )
    monkeypatch.setattr("vdisplay.control.vision_ocr.ocr_png", lambda _png: [])

    payload = map_refresh(map_path=str(path), monitor="HDMI-1", force=True)

    assert payload.get("write_skipped") is not True
    updated = load_gui_map(path)
    assert updated.monitor == "HDMI-1"
    assert updated.rotation == "normal"
    assert updated.capture_meta.get("source") == "HDMI-1"


def test_assess_map_drift_refresh_required_on_many_missing() -> None:
    from vdisplay.control.gui_map_diff import ElementDrift, GuiMapDiff

    payload = GuiMapDiff(
        ok=False,
        drifted=True,
        summary={"ok": 2, "missing": 5, "bounds": 1, "fingerprint": 0},
        elements=[
            ElementDrift("chat", "missing", "OCR anchor not found near stored bounds"),
            ElementDrift("message", "bounds", "bounds moved 20px"),
        ],
    )
    recommendation, actionable, keys = assess_map_drift(payload)
    assert recommendation == "refresh_required"
    assert actionable is True
    assert keys["chat"] == "missing"
    assert keys["message"] == "bounds"


def test_build_gui_map_scoped_crop_filters_outside_boxes(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.control.gui_map import GuiMapBounds, build_gui_map_from_ocr

    png = _fake_png()
    all_boxes = [
        OcrTextBox("Inside", ControlBounds(x=20, y=30, width=60, height=16), 0.9),
        OcrTextBox("Outside", ControlBounds(x=300, y=150, width=60, height=16), 0.9),
    ]
    monkeypatch.setattr("vdisplay.control.vision_ocr.ocr_png", lambda _png: all_boxes)
    scope = GuiMapBounds(x=0, y=0, width=200, height=100)
    pack = build_gui_map_from_ocr(
        png,
        {"width": 400, "height": 200},
        region_id="chat",
        scope_bounds=scope,
    )
    assert set(pack.elements) == {"inside"}
    assert pack.regions["chat"].scope_bounds.width == 200


def test_map_capture_prefers_agent_screencast(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.application.services.map import _capture

    png = _fake_png()
    monkeypatch.setattr(
        "vdisplay.application.services.map._capture_via_agent",
        lambda **_k: (png, {"method": "agent-screencast", "source": "DP-2"}),
    )

    def _fail_host(**_kwargs):
        raise AssertionError("capture_host_png should not run when agent capture succeeds")

    monkeypatch.setattr("vdisplay.capture.host.capture_host_png", _fail_host)
    captured, meta = _capture(display=":0", monitor="DP-2")
    assert captured == png
    assert meta["source"] == "DP-2"


def test_map_capture_requires_screencast_when_agent_running(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.application.services.map import _capture
    from vdisplay.exceptions import VDisplayError

    monkeypatch.setattr(
        "vdisplay.agent_config.resolve_agent_url",
        lambda **_k: "http://127.0.0.1:8765",
    )

    class _Client:
        def __init__(self, *_args, **_kwargs):
            pass

        def screencast_status(self):
            return {"ready": False}

    monkeypatch.setattr("vdisplay.client.AgentClient", _Client)

    with pytest.raises(VDisplayError, match="screencast not ready"):
        _capture(display=":0", monitor="DP-2")
