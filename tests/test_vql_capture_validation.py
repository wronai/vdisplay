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


def test_jetbrains_capture_rejects_missing_window_title(monkeypatch) -> None:
    # vision-defer would suppress this reject; assert the baseline (vision off)
    monkeypatch.delenv("KORU_VDISPLAY_LLM_VISION_DECISION", raising=False)
    monkeypatch.delenv("VDISPLAY_VISION_CHAT_DETECT", raising=False)
    layers = [
        {
            "id": "window_0",
            "kind": "window",
            "text": "",
            "bbox": {"x": 0, "y": 0, "w": 2048, "h": 1280},
        }
    ]
    out = validate_vql_capture(
        layers=layers,
        ide="jetbrains",
        reverse={"canvas": {"width": 2048, "height": 1280}},
    )
    assert out["capture_confirmed"] is False
    assert out["ok_for_drive"] is False
    assert out["ide_window_warning"]["reason"] == "missing_window_title"
    assert "missing_window_title" in out["reasons"]


def test_body_ide_mentions_ignores_window_layer() -> None:
    layers = [
        {"kind": "window", "text": "project - Cursor"},
        {"kind": "label", "text": "Upewnij sie ze PyCharm jest na wierzchu"},
    ]
    mentions = body_ide_mentions(ide="jetbrains", layers=layers)
    assert any("PyCharm" in item for item in mentions)


def _editor_breadcrumb_layers():
    # DP-1: PyCharm editor breadcrumb on the left, no "PyCharm" in the window title
    return [
        {
            "id": "window_0",
            "kind": "window",
            "text": "koru – main.py – Current File",
            "bbox": {"x": 0, "y": 0, "w": 2560, "h": 1600},
        }
    ]


def test_non_competing_title_deferred_to_vision_when_enabled(monkeypatch) -> None:
    monkeypatch.setenv("KORU_VDISPLAY_LLM_VISION_DECISION", "1")
    out = validate_vql_capture(
        layers=_editor_breadcrumb_layers(),
        ide="jetbrains",
        reverse={"canvas": {"width": 2560, "height": 1600}},
    )
    assert out["vision_deferred_window_mismatch"] is True
    assert out["capture_confirmed"] is True
    assert out["ok_for_drive"] is True
    assert "ide_window_mismatch_deferred_to_vision" in out["reasons"]


def test_non_competing_title_still_blocks_without_vision(monkeypatch) -> None:
    monkeypatch.delenv("KORU_VDISPLAY_LLM_VISION_DECISION", raising=False)
    monkeypatch.delenv("VDISPLAY_VISION_CHAT_DETECT", raising=False)
    out = validate_vql_capture(
        layers=_editor_breadcrumb_layers(),
        ide="jetbrains",
        reverse={"canvas": {"width": 2560, "height": 1600}},
    )
    assert out["vision_deferred_window_mismatch"] is False
    assert out["capture_confirmed"] is False


def test_competing_ide_never_deferred_even_under_vision(monkeypatch) -> None:
    monkeypatch.setenv("KORU_VDISPLAY_LLM_VISION_DECISION", "1")
    layers = [
        {
            "id": "window_0",
            "kind": "window",
            "text": "project - ts - Cursor",
            "bbox": {"x": 0, "y": 0, "w": 2560, "h": 1600},
        }
    ]
    out = validate_vql_capture(
        layers=layers,
        ide="jetbrains",
        reverse={"canvas": {"width": 2560, "height": 1600}},
    )
    assert out["vision_deferred_window_mismatch"] is False
    assert out["capture_confirmed"] is False


def test_missing_window_title_deferred_under_vision(monkeypatch) -> None:
    # Unstable OCR (no window-title layer) on a multi-panel monitor: vision's own
    # confidence guard is the safety net, so defer instead of hard-blocking.
    monkeypatch.setenv("KORU_VDISPLAY_LLM_VISION_DECISION", "1")
    layers = [
        {"id": "label_0", "kind": "label", "text": "Ask AI", "bbox": {"x": 10, "y": 10, "w": 40, "h": 12}},
    ]
    out = validate_vql_capture(
        layers=layers,
        ide="jetbrains",
        reverse={"canvas": {"width": 2560, "height": 1600}},
    )
    # under vision the VQL structure quality is not a gate (vision reads the PNG)
    assert out["vision_deferred_window_mismatch"] is True
    assert out["capture_confirmed"] is True
    assert "ide_window_mismatch_deferred_to_vision" in out["reasons"]


def test_missing_window_title_still_blocks_without_vision(monkeypatch) -> None:
    monkeypatch.delenv("KORU_VDISPLAY_LLM_VISION_DECISION", raising=False)
    monkeypatch.delenv("VDISPLAY_VISION_CHAT_DETECT", raising=False)
    layers = [
        {"id": "label_0", "kind": "label", "text": "Ask AI", "bbox": {"x": 10, "y": 10, "w": 40, "h": 12}},
    ]
    out = validate_vql_capture(
        layers=layers,
        ide="jetbrains",
        reverse={"canvas": {"width": 2560, "height": 1600}},
    )
    assert out["vision_deferred_window_mismatch"] is False
    assert out["capture_confirmed"] is False
