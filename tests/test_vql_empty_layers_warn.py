from __future__ import annotations

import warnings

import pytest

from vdisplay.integrations.screen_context import ScreenContext
from vdisplay.integrations.vql_bridge import _warn_empty_vql_layers, write_vql_artifacts


def test_warn_empty_vql_layers_when_imgl_missing(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    png = tmp_path / "shot.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n")
    ctx = ScreenContext(
        image_path=str(png),
        capture={"path": str(png), "width": 100, "height": 50},
        fingerprint="abc",
    )
    monkeypatch.setenv("VDISPLAY_IMGL", "1")
    monkeypatch.setattr("vdisplay.integrations.imgl_bridge.imgl_available", lambda: False)
    program = {"metadata": {"render_intent": {"layers": []}}}

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _warn_empty_vql_layers(ctx, program)

    assert any("imgl is not installed" in str(w.message) for w in caught)


def test_write_vql_warns_on_empty_layers(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    png = tmp_path / "shot.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82")
    ctx = ScreenContext(
        image_path=str(png),
        capture={"path": str(png), "width": 1, "height": 1},
        fingerprint="warn-test",
    )
    monkeypatch.setenv("VDISPLAY_IMGL", "1")
    monkeypatch.setattr("vdisplay.integrations.imgl_bridge.imgl_available", lambda: False)
    monkeypatch.setattr(
        "vdisplay.integrations.vql_bridge.context_to_vql_program",
        lambda c: {"version": "1.0", "metadata": {"render_intent": {"layers": []}}},
    )
    monkeypatch.setattr(
        "vdisplay.integrations.vql_bridge.reverse_generation_descriptor",
        lambda c: {"layers": []},
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        write_vql_artifacts(ctx, vql_path=tmp_path / "shot.png.vql.json")

    assert any("imgl is not installed" in str(w.message) for w in caught)
