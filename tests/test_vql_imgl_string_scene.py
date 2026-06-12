from __future__ import annotations

import json

from vdisplay.integrations.vql_bridge import _build_imgl_layers, _extract_imgl_scene


def test_extract_imgl_scene_from_json_string_with_windows() -> None:
    payload = {
        "version": "1.0",
        "scene": {"width": 2048, "height": 1280},
        "windows": [
            {
                "id": "window_0",
                "title": "PyCharm",
                "bbox": {"x": 0, "y": 0, "w": 100, "h": 50},
                "elements": [
                    {
                        "id": "btn_0",
                        "type": "button",
                        "text": "Run",
                        "bbox": {"x": 10, "y": 10, "w": 20, "h": 10},
                    }
                ],
            }
        ],
    }
    imgl = {"ok": True, "scene": json.dumps(payload)}
    scene = _extract_imgl_scene(imgl)
    assert scene is not None
    assert len(scene.get("windows") or []) == 1
    layers = _build_imgl_layers(imgl)
    assert len(layers) >= 2
    assert any(layer.get("text") == "Run" for layer in layers)
