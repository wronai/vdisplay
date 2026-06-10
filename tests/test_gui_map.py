"""PR-26 — GUI Map Pack model, export, and map-based control."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vdisplay.control.action_bounds import action_bounds_for_vision, click_point_for_vision
from vdisplay.control.gui_map import (
    GuiMapBounds,
    build_gui_map_from_ocr,
    element_from_ocr_box,
    load_gui_map,
    map_element_to_node,
    resolve_map_element,
    save_gui_map,
    verify_hints_from_map_element,
)
from vdisplay.control.gui_map_export import render_map_markdown, render_map_svg
from vdisplay.control.models import ControlBounds
from vdisplay.control.vision_ocr import OcrTextBox


def _fake_png() -> bytes:
    from PIL import Image
    import io

    image = Image.new("RGB", (400, 200), color=(240, 240, 240))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def test_action_bounds_expands_narrow_ocr_box() -> None:
    raw = ControlBounds(x=100, y=200, width=40, height=20)
    action = action_bounds_for_vision(raw)
    assert action.width == 320
    assert click_point_for_vision(raw) == (260, 210)


def test_element_from_ocr_box_records_raw_and_action_bounds() -> None:
    box = OcrTextBox("Ask anything", ControlBounds(x=10, y=20, width=80, height=18), 0.91)
    element = element_from_ocr_box(
        box,
        element_id="ask_anything",
        region_id="screen",
        capture_meta={"width": 400, "height": 200, "source": "DP-2", "rotation": "left"},
        monitor="DP-2",
        rotation="left",
        png=_fake_png(),
    )
    assert element.raw_bounds.width == 80
    assert element.action_bounds.width == 320
    assert element.click_point.x == element.action_bounds.center[0]
    assert element.tile_fingerprint is not None


def test_build_and_load_gui_map_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    boxes = [
        OcrTextBox("Chat", ControlBounds(x=5, y=5, width=40, height=16), 0.95),
        OcrTextBox("Ask anything", ControlBounds(x=5, y=40, width=120, height=16), 0.92),
    ]

    monkeypatch.setattr("vdisplay.control.vision_ocr.ocr_png", lambda _png: boxes)
    pack = build_gui_map_from_ocr(
        _fake_png(),
        {"width": 400, "height": 200, "source": "DP-2", "rotation": "left"},
        monitor="DP-2",
        rotation="left",
        region_id="pycharm.ai_chat",
    )
    path = tmp_path / "map.json"
    save_gui_map(path, pack)
    loaded = load_gui_map(path)
    assert loaded.monitor == "DP-2"
    assert "pycharm.ai_chat" in loaded.regions
    assert len(loaded.elements) == 2
    element = resolve_map_element(loaded, "ask_anything")
    node = map_element_to_node(element)
    assert node.state["map"] is True
    assert node.bounds.width == element.action_bounds.width


def test_map_markdown_and_svg_export() -> None:
    box = OcrTextBox("Go", ControlBounds(x=1, y=2, width=40, height=20), 0.9)
    element = element_from_ocr_box(
        box,
        element_id="go",
        region_id="screen",
        capture_meta={"width": 400, "height": 200},
        monitor="DP-1",
        rotation="normal",
        png=_fake_png(),
    )
    from vdisplay.control.gui_map import GuiMapPack, GuiMapRegion

    pack = GuiMapPack(
        monitor="DP-1",
        elements={"go": element},
        regions={
            "screen": GuiMapRegion(
                id="screen",
                label="screen",
                scope_bounds=GuiMapBounds(x=0, y=0, width=400, height=200),
                elements=["go"],
            )
        },
    )
    md = render_map_markdown(pack, title="test map")
    assert "Action bounds" in md
    assert "go" in md
    svg = render_map_svg(_fake_png(), pack)
    assert b'<svg' in svg
    assert b'go-action' in svg


def test_verify_hints_from_map_element() -> None:
    box = OcrTextBox("Count: 0", ControlBounds(x=1, y=2, width=40, height=20), 0.9)
    element = element_from_ocr_box(
        box,
        element_id="counter",
        region_id="panel",
        capture_meta={},
        monitor=None,
        rotation=None,
    )
    hints = verify_hints_from_map_element(element)
    assert hints["verify_label"] == "Count: 0"


def test_map_based_control_click_uses_stored_click_point(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from vdisplay.application.services.control import control_click

    box = OcrTextBox("Ask anything", ControlBounds(x=10, y=20, width=80, height=18), 0.91)
    element = element_from_ocr_box(
        box,
        element_id="input",
        region_id="chat",
        capture_meta={"width": 400, "height": 200},
        monitor="DP-2",
        rotation="left",
    )
    from vdisplay.control.gui_map import GuiMapPack, GuiMapRegion, save_gui_map

    pack = GuiMapPack(
        monitor="DP-2",
        rotation="left",
        elements={"input": element},
        regions={
            "chat": GuiMapRegion(
                id="chat",
                label="chat",
                scope_bounds=GuiMapBounds(x=0, y=0, width=400, height=200),
                elements=["input"],
            )
        },
    )
    path = tmp_path / "map.json"
    save_gui_map(path, pack)

    clicked: list[tuple[int, int]] = []

    class FakeVision:
        name = "vision"

        def snapshot(self, **kwargs):
            from vdisplay.control.models import ControlSnapshot

            return ControlSnapshot(backend="vision", window_id=None, app_label=None, nodes={}, root_ids=[])

        def invoke(self, element_id: str, *, action: str | None = None):
            return {"ok": True, "element_id": element_id}

        def focus(self, element_id: str):
            return {"ok": True}

        def set_value(self, element_id: str, value: str):
            return {"ok": True, "value": value}

        def _pointer_click_at(self, bounds, *, capture_meta=None, click_point=None):
            clicked.append(click_point or bounds.center)
            return {"ok": True, "method": "test", "x": clicked[-1][0], "y": clicked[-1][1]}

    class FakeRouting:
        verify_mode = "semantic"
        verify_provider = "vision"

        def to_dict(self):
            return {"selected_provider": "vision"}

    monkeypatch.setattr(
        "vdisplay.application.services.control.evaluate_provider_routing",
        lambda *args, **kwargs: FakeRouting(),
    )
    monkeypatch.setattr(
        "vdisplay.control.providers.vision.VisionStubProvider",
        lambda **kwargs: FakeVision(),
    )
    monkeypatch.setattr(
        "vdisplay.application.services.control._capture_before_state",
        lambda **_k: (None, None),
    )
    monkeypatch.setattr(
        "vdisplay.application.services.control._perform_action",
        lambda provider, action, target, value: provider._pointer_click_at(
            target.bounds,
            capture_meta=(target.state or {}).get("capture"),
            click_point=(
                int((target.state or {}).get("click_point", {}).get("x") or 0),
                int((target.state or {}).get("click_point", {}).get("y") or 0),
            ),
        ),
    )
    monkeypatch.setattr(
        "vdisplay.control.verifier.VerifierPipeline.verify_after_action",
        lambda self, ctx: type(
            "VR",
            (),
            {
                "verified": True,
                "confidence": 1.0,
                "mode": "semantic",
                "reasons": [],
                "semantic": {"verified": True, "state_diff": {}},
                "visual": None,
                "to_dict": lambda self: {},
            },
        )(),
    )

    payload = control_click(
        backend="vision",
        map_path=str(path),
        map_target="input",
        verify=False,
    )
    assert payload["ok"] is True
    assert clicked == [(element.click_point.x, element.click_point.y)]
