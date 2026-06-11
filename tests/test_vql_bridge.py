from __future__ import annotations

from vdisplay.integrations.vql_bridge import _build_imgl_layers


def test_build_imgl_layers_flattens_window_elements_and_ocr() -> None:
    imgl = {
        "ok": True,
        "scene": {
            "windows": [
                {
                    "id": "window_0",
                    "bbox": {"x": 0, "y": 0, "w": 100, "h": 50},
                    "elements": [
                        {
                            "id": "window_0-input-1",
                            "type": "input",
                            "text": "editor",
                            "bbox": {"x": 10, "y": 20, "w": 80, "h": 10},
                            "confidence": 0.9,
                        }
                    ],
                }
            ],
            "ocr_boxes": [{"text": "Ask", "bbox": {"x": 5, "y": 5, "w": 20, "h": 10}, "confidence": 90.0}],
        },
    }
    layers = _build_imgl_layers(imgl)
    assert len(layers) >= 3
    editor = next(item for item in layers if item.get("text") == "editor")
    assert editor["click_center"] == {"x": 50, "y": 25}
    ask = next(item for item in layers if item.get("text") == "Ask")
    assert ask["kind"] == "ocr"
