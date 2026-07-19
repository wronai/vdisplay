from __future__ import annotations

from vdisplay.integrations import normalize_vql_ui_elements


def test_normalizes_render_intent_layers_and_derives_center() -> None:
    payload = {
        "metadata": {
            "render_intent": {
                "layers": [
                    {
                        "id": "panel-1",
                        "kind": "panel",
                        "text": "Chat",
                        "bbox": {"x": 700, "y": 300, "w": 300, "h": 280},
                        "confidence": 0.9,
                    }
                ]
            }
        }
    }

    assert normalize_vql_ui_elements(payload) == [
        {
            "id": "panel-1",
            "role": "panel",
            "label": "Chat",
            "bounds": {"x": 700, "y": 300, "w": 300, "h": 280},
            "click_center": {"x": 850, "y": 440},
            "metadata": {"confidence": 0.9},
        }
    ]


def test_normalizes_fresh_dict_bbox_to_capture_local_space() -> None:
    payload = {
        "elements": [
            {
                "id": 7,
                "kind": "window",
                "label": "PyCharm",
                "bbox": {"left": 86, "top": 24, "right": 2004, "bottom": 1260},
                "center": [1045, 642],
            }
        ]
    }

    element = normalize_vql_ui_elements(payload)[0]
    assert element["id"] == "7"
    assert element["bounds"] == {
        "x": 86,
        "y": 24,
        "width": 1918,
        "height": 1236,
        "coordinate_space": "capture_frame_local",
    }
    assert element["click_center"] == {"x": 1045, "y": 642}


def test_fallback_center_is_explicit_and_deterministic() -> None:
    payload = {"elements": [{"role": "unknown"}]}

    first = normalize_vql_ui_elements(payload, fallback_center=(1024, 640))
    retry = normalize_vql_ui_elements(payload, fallback_center=(1024, 640))

    assert first == retry
    assert first[0]["click_center"] == {"x": 1024, "y": 640}


def test_unwraps_vql_program_payload() -> None:
    payload = {
        "vql": {
            "program": {
                "layers": [
                    {
                        "id": "input-1",
                        "role": "input",
                        "bounds": [10, 20, 110, 60],
                        "click_center": {"x": 60, "y": 40},
                    }
                ]
            }
        }
    }

    assert normalize_vql_ui_elements(payload)[0]["click_center"] == {"x": 60, "y": 40}
