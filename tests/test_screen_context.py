"""ScreenContext and IMGL/VQL integration tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vdisplay.integrations.pipeline import observe_enabled, observe_screen
from vdisplay.integrations.screen_context import ScreenContext, screen_context_from_capture
from vdisplay.integrations.vql_bridge import context_to_vql_program, reverse_generation_descriptor


def test_screen_context_from_capture_builds_fingerprint(tmp_path: Path) -> None:
    png = tmp_path / "screen.png"
    png.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
        b"\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    ctx = screen_context_from_capture(
        {"path": str(png), "display": ":0", "width": 1, "height": 1, "source": "test"},
    )
    assert ctx.image_path == str(png)
    assert ctx.capture["display"] == ":0"
    assert len(ctx.fingerprint) == 16


def test_context_to_vql_program_includes_capture_and_reverse(tmp_path: Path) -> None:
    ctx = ScreenContext(
        image_path=str(tmp_path / "screen.png"),
        capture={"width": 800, "height": 600, "source": "vdisplay", "display": ":0"},
        nl="Chat window with message field.",
        environment={"routing": {"selected_provider": "vision", "application_profile": "chat@app"}},
    )
    ctx.compute_fingerprint()
    program = context_to_vql_program(ctx)
    assert program["metadata"]["capture"]["width"] == 800
    assert program["metadata"]["environment"]["routing"]["selected_provider"] == "vision"
    reverse = reverse_generation_descriptor(ctx)
    assert reverse["nl"] == "Chat window with message field."
    assert reverse["canvas"]["width"] == 800


def test_context_to_vql_program_validates_scene_layers_when_render_empty(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    png = tmp_path / "screen.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
    layer = {
        "id": "window_0",
        "kind": "window",
        "text": "project - PyCharm",
        "bbox": {"x": 0, "y": 0, "w": 800, "h": 600},
        "click_center": {"x": 400, "y": 300},
    }
    ctx = ScreenContext(
        image_path=str(png),
        capture={"width": 800, "height": 600, "source": "vdisplay"},
        nl="PyCharm window.",
    )
    ctx.compute_fingerprint()
    monkeypatch.setenv("VDISPLAY_CAPTURE_VALIDATE_IDE", "jetbrains")
    monkeypatch.setattr(
        "vdisplay.integrations.vql_bridge._try_from_screen_context",
        lambda _ctx: {
            "version": "1.0",
            "scene": {"width": 800, "height": 600, "layers": [layer]},
            "layers": [layer],
            "metadata": {"render_intent": {"canvas": {"width": 800, "height": 600}, "layers": []}},
        },
    )

    program = context_to_vql_program(ctx)
    validation = program["metadata"]["capture_validation"]

    assert validation["capture_confirmed"] is True
    assert validation["structure"]["layer_count"] == 1
    assert program["metadata"]["render_intent"]["layers"] == [layer]


def test_observe_screen_writes_sidecar(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("VDISPLAY_IMGL", "0")
    monkeypatch.setenv("VDISPLAY_VQL", "0")
    png = tmp_path / "screen.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
    ctx = observe_screen(
        image_path=png,
        capture_meta={"path": str(png), "width": 10, "height": 10, "source": "test"},
        include_imgl=False,
        include_vql=False,
        write_sidecar=True,
    )
    sidecar = png.with_suffix(png.suffix + ".context.json")
    assert sidecar.is_file()
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    assert payload["fingerprint"] == ctx.fingerprint


def test_observe_enabled_explicit_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_OBSERVE", "1")
    assert observe_enabled() is True
    monkeypatch.setenv("VDISPLAY_OBSERVE", "0")
    assert observe_enabled() is False
