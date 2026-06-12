from __future__ import annotations

from vdisplay.integrations.vql_capture_validation import (
    body_ide_mentions,
    validate_vql_capture,
    validate_vql_structure,
)


def test_validate_vql_structure_flags_empty_layers() -> None:
    out = validate_vql_structure(layers=[], reverse={"canvas": {"width": 2048, "height": 1280}})
    assert out["structure_ok"] is False
    assert "empty_vql_layers" in out["reasons"]
    assert "missing_window_layer" in out["reasons"]


def test_jetbrains_capture_rejects_cursor_window_title() -> None:
    layers = [
        {
            "id": "window_0",
            "kind": "window",
            "text": "automation-gap-analysis - ts - Cursor",
            "bbox": {"x": 0, "y": 0, "w": 2048, "h": 1280},
        },
        {
            "id": "window_0-text-81",
            "kind": "label",
            "text": "PyCharm",
            "bbox": {"x": 784, "y": 784, "w": 69, "h": 17},
        },
    ]
    out = validate_vql_capture(
        layers=layers,
        ide="jetbrains",
        reverse={"canvas": {"width": 2048, "height": 1280}},
    )
    assert out["capture_confirmed"] is False
    assert out["body_false_positive"] is True
    assert "PyCharm" in " ".join(out["body_ide_mentions"])
    assert "Cursor" in out["ide_window_warning"]["window_titles"][0]
    assert "ide_window_mismatch" in out["reasons"]
    assert "body_mentions_target_ide_not_window_title" in out["reasons"]


def test_jetbrains_capture_accepts_pycharm_window_title() -> None:
    layers = [
        {
            "id": "window_0",
            "kind": "window",
            "text": "koru – main.py – PyCharm",
            "bbox": {"x": 0, "y": 0, "w": 2048, "h": 1280},
        }
    ]
    out = validate_vql_capture(
        layers=layers,
        ide="jetbrains",
        reverse={"canvas": {"width": 2048, "height": 1280}},
    )
    assert out["capture_confirmed"] is True
    assert out["ok_for_drive"] is True
    assert out["ide_window_warning"] is None


def test_body_ide_mentions_ignores_window_layer() -> None:
    layers = [
        {"kind": "window", "text": "project - Cursor"},
        {"kind": "label", "text": "Upewnij sie ze PyCharm jest na wierzchu"},
    ]
    mentions = body_ide_mentions(ide="jetbrains", layers=layers)
    assert any("PyCharm" in item for item in mentions)
