from __future__ import annotations

from pathlib import Path

import pytest

from vdisplay.integrations import imgl_bridge


def test_import_imgl_api_accepts_submodule_layout() -> None:
    api = imgl_bridge._import_imgl_api()
    if api is None:
        pytest.skip("imgl not installed in test environment")
    ImglConfig, analyze, scene_to_json = api
    assert ImglConfig is not None
    assert callable(analyze)
    assert callable(scene_to_json)


def test_analyze_with_imgl_missing_file() -> None:
    result = imgl_bridge.analyze_with_imgl("/tmp/does-not-exist-vdisplay-imgl.png")
    assert result["ok"] is False
    assert "not found" in result["error"]


def test_imgl_available_respects_disable_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_IMGL", "0")
    assert imgl_bridge.imgl_available() is False


def test_analyze_with_imgl_on_tiny_png(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    if not imgl_bridge.imgl_available():
        pytest.skip("imgl not installed")
    png = tmp_path / "tiny.png"
    png.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
        b"\x01\x01\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    monkeypatch.setenv("VDISPLAY_IMGL_SKIP_BLANK", "1")
    result = imgl_bridge.analyze_with_imgl(png, use_cache=False)
    assert "ok" in result
    if result.get("ok"):
        assert isinstance(result.get("scene"), dict)
    else:
        assert isinstance(result.get("error"), str)


def test_scene_to_dict_parses_json_string() -> None:
    payload = imgl_bridge._scene_to_dict('{"elements": [{"id": "a"}], "windows": []}', lambda s: s)
    assert payload.get("elements") and payload["elements"][0]["id"] == "a"
