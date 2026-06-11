from __future__ import annotations

from vdisplay.integrations.vql_bridge import _build_imgl_layers, _extract_imgl_scene


def test_extract_imgl_scene_from_img2nl_metadata() -> None:
    imgl = {
        "img2nl": {
            "ok": True,
            "metadata": {
                "scene": {
                    "windows": [
                        {
                            "id": "window_0",
                            "bbox": {"x": 0, "y": 0, "w": 100, "h": 50},
                            "elements": [],
                        }
                    ]
                }
            },
        }
    }
    scene = _extract_imgl_scene(imgl)
    assert scene is not None
    layers = _build_imgl_layers(imgl)
    assert len(layers) >= 1
    assert layers[0]["id"] == "window_0"
