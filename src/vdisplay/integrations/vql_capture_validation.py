"""Validate VQL capture metadata for autonomy loops (IDE window title, structure, chat hints)."""

from __future__ import annotations

import os
import re
from typing import Any

_IDE_WINDOW_TITLE_TOKENS: dict[str, tuple[str, ...]] = {
    "cursor": ("cursor",),
    "windsurf": ("windsurf",),
    "vscode": ("visual studio code", "vscode"),
    "vscodium": ("vscodium",),
    "antigravity": ("antigravity",),
    "zed": ("zed",),
    "jetbrains": ("jetbrains", "pycharm", "intellij", "idea", "webstorm", "goland", "clion", "rider"),
    "pycharm": ("pycharm", "jetbrains"),
    "idea": ("intellij", "idea", "jetbrains"),
}

_COMPETING_IDE_WINDOW_TOKENS: dict[str, tuple[str, ...]] = {
    "jetbrains": ("cursor", "visual studio code", "vscode", "windsurf", "vscodium", "antigravity", "zed"),
    "pycharm": ("cursor", "visual studio code", "vscode", "windsurf"),
    "idea": ("cursor", "visual studio code", "vscode", "windsurf"),
    "cursor": ("pycharm", "intellij", "jetbrains", "webstorm"),
    "windsurf": ("pycharm", "intellij", "jetbrains"),
    "vscode": ("pycharm", "intellij", "jetbrains", "cursor"),
}

_TERMINAL_LABEL_RE = re.compile(
    r"\b(terminal|shell|bash|problems|output|debug|console|export|unset|zsh|fish)\b",
    re.I,
)

_IDE_BODY_TOKEN_RE: dict[str, re.Pattern[str]] = {
    "jetbrains": re.compile(r"\b(pycharm|intellij|jetbrains|webstorm|goland|clion|rider)\b", re.I),
    "cursor": re.compile(r"\bcursor\b", re.I),
}


def expected_ide_from_env() -> str:
    for key in ("VDISPLAY_CAPTURE_VALIDATE_IDE", "KORU_VDISPLAY_IDE", "VDISPLAY_IDE"):
        val = os.environ.get(key, "").strip().lower()
        if val:
            return val
    return ""


def _canonical_ide(ide: str) -> str:
    raw = (ide or "").strip().lower()
    aliases = {
        "pycharm": "jetbrains",
        "idea": "jetbrains",
        "intellij": "jetbrains",
        "jb": "jetbrains",
    }
    return aliases.get(raw, raw)


def window_titles_from_layers(layers: list[dict[str, Any]]) -> list[str]:
    titles: list[str] = []
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        role = str(layer.get("role") or layer.get("kind") or "").lower()
        if role != "window":
            continue
        title = str(layer.get("label") or layer.get("text") or layer.get("title") or "").strip()
        if title:
            titles.append(title)
    return titles


def _center_from_dict(center: Any) -> tuple[int, int] | None:
    """Safely extract (x, y) from a center dict."""
    if not isinstance(center, dict):
        return None
    try:
        return int(center.get("x") or 0), int(center.get("y") or 0)
    except (TypeError, ValueError):
        return None


def _bbox_center(bbox: Any) -> tuple[int, int] | None:
    """Compute center (x, y) from a bbox dict."""
    if not isinstance(bbox, dict):
        return None
    try:
        x = int(bbox.get("x") or 0)
        y = int(bbox.get("y") or 0)
        w = int(bbox.get("w") or bbox.get("width") or 0)
        h = int(bbox.get("h") or bbox.get("height") or 0)
    except (TypeError, ValueError):
        return None
    if w <= 0 or h <= 0:
        return None
    return x + w // 2, y + h // 2


def _layer_center(layer: dict[str, Any]) -> tuple[int, int] | None:
    center = _center_from_dict(layer.get("click_center") or layer.get("center"))
    if center is not None:
        return center
    return _bbox_center(layer.get("bbox") or layer.get("bounds"))


def _layer_label(layer: dict[str, Any]) -> str:
    return str(layer.get("label") or layer.get("text") or "").strip()


def ide_window_warning(*, ide: str, layers: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Match only the window layer title — not breadcrumb/body OCR."""
    canon = _canonical_ide(ide)
    if canon in {"", "auto"}:
        return None
    tokens = _IDE_WINDOW_TITLE_TOKENS.get(canon, ())
    if not tokens:
        return None
    titles = window_titles_from_layers(layers)
    if not titles:
        return {
            "ide": canon,
            "expected_tokens": list(tokens),
            "window_titles": [],
            "reason": "missing_window_title",
            "message": (
                f"VQL capture has no foreground window title for {canon}. "
                "Focus the target IDE and refresh observe before drive."
            ),
        }

    joined = " | ".join(titles).lower()
    competing = _COMPETING_IDE_WINDOW_TOKENS.get(canon, ())
    if any(comp in joined for comp in competing):
        return {
            "ide": canon,
            "expected_tokens": list(tokens),
            "window_titles": titles,
            "competing_detected": list(competing),
            "message": (
                f"VQL capture foreground window looks like a different IDE than {canon}: "
                f"title(s)={titles!r}. Re-focus {canon} on the capture monitor and refresh observe."
            ),
        }
    if any(token in joined for token in tokens):
        return None
    return {
        "ide": canon,
        "expected_tokens": list(tokens),
        "window_titles": titles,
        "message": (
            f"VQL capture does not look like {canon}: window title(s)={titles!r}. "
            f"Focus the correct IDE on the target monitor before drive."
        ),
    }


def body_ide_mentions(*, ide: str, layers: list[dict[str, Any]]) -> list[str]:
    """OCR mentions of the target IDE outside the window title layer (false-positive risk)."""
    canon = _canonical_ide(ide)
    pattern = _IDE_BODY_TOKEN_RE.get(canon)
    if pattern is None:
        return []
    found: list[str] = []
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        role = str(layer.get("role") or layer.get("kind") or "").lower()
        if role == "window":
            continue
        label = _layer_label(layer)
        if label and pattern.search(label):
            found.append(label[:120])
    # dedupe preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for item in found:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique[:12]


def chat_composer_candidates(
    layers: list[dict[str, Any]],
    *,
    min_y: int = 850,
    min_x: int = 400,
) -> list[dict[str, Any]]:
    """Heuristic chat inputs in the lower/right pane (excludes terminal panes)."""
    out: list[dict[str, Any]] = []
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        role = str(layer.get("role") or layer.get("kind") or "").lower()
        if role not in {"input", "textarea", "textbox"}:
            continue
        center = _layer_center(layer)
        if center is None:
            continue
        cx, cy = center
        if cy < min_y or cx < min_x:
            continue
        label = _layer_label(layer)
        if label and _TERMINAL_LABEL_RE.search(label):
            continue
        out.append(
            {
                "id": layer.get("id"),
                "label": label or None,
                "click_center": {"x": cx, "y": cy},
                "role": role,
            }
        )
    return out[:8]


def validate_vql_structure(
    *,
    layers: list[dict[str, Any]],
    reverse: dict[str, Any] | None = None,
) -> dict[str, Any]:
    canvas = (reverse or {}).get("canvas") or {}
    width = int(canvas.get("width") or 0)
    height = int(canvas.get("height") or 0)
    window_layers = [layer for layer in layers if str(layer.get("kind") or layer.get("role") or "").lower() == "window"]
    reasons: list[str] = []
    if not layers:
        reasons.append("empty_vql_layers")
    if not window_layers:
        reasons.append("missing_window_layer")
    if width <= 0 or height <= 0:
        reasons.append("missing_canvas_size")
    return {
        "layer_count": len(layers),
        "window_layer_count": len(window_layers),
        "canvas": {"width": width, "height": height},
        "structure_ok": not reasons,
        "reasons": reasons,
    }


def _vision_decision_enabled() -> bool:
    truthy = {"1", "true", "yes", "on"}
    for var in ("KORU_VDISPLAY_LLM_VISION_DECISION", "VDISPLAY_VISION_CHAT_DETECT"):
        if (os.environ.get(var) or "").strip().lower() in truthy:
            return True
    return False


def _warn_is_competing_ide(warn: dict[str, Any] | None) -> bool:
    """True when the window title names a *different* IDE (never override)."""
    if not warn:
        return False
    return bool(warn.get("competing_detected"))


def _warn_is_vision_deferrable(warn: dict[str, Any] | None) -> bool:
    """Only a *present* title that fails to match (editor breadcrumb / right-docked
    chat panel) may defer to vision. A missing title means the capture itself may
    have failed — never defer that; a competing IDE is never deferrable either."""
    if not warn:
        return False
    if warn.get("reason") == "missing_window_title":
        return False
    if _warn_is_competing_ide(warn):
        return False
    return bool(warn.get("window_titles"))


def validate_vql_capture(
    *,
    layers: list[dict[str, Any]],
    ide: str = "",
    reverse: dict[str, Any] | None = None,
    nl: str | None = None,
) -> dict[str, Any]:
    """Full capture validation block stored in VQL sidecar metadata."""
    expected = _canonical_ide(ide or expected_ide_from_env())
    structure = validate_vql_structure(layers=layers, reverse=reverse)
    titles = window_titles_from_layers(layers)
    warn = ide_window_warning(ide=expected, layers=layers) if expected else None
    body = body_ide_mentions(ide=expected, layers=layers) if expected else []
    body_false_positive = bool(body and warn is not None)
    chat = chat_composer_candidates(layers)

    # When vision LLM will locate the chat input from the screenshot, a title
    # that merely fails to say "PyCharm" (editor breadcrumb, or a right-docked
    # Qoder/AI chat panel) is not a capture-confirmation blocker — the vision
    # layer has its own confidence + geometry guards. A title naming a
    # *competing* IDE still blocks: typing into the wrong IDE must never happen.
    vision_deferred = bool(
        _vision_decision_enabled()
        and _warn_is_vision_deferrable(warn)
    )
    blocking_warn = None if vision_deferred else warn

    reasons: list[str] = list(structure.get("reasons") or [])
    if expected and warn is not None:
        reasons.append(str(warn.get("reason") or "ide_window_mismatch"))
    if vision_deferred:
        reasons.append("ide_window_mismatch_deferred_to_vision")
    if body_false_positive:
        reasons.append("body_mentions_target_ide_not_window_title")

    capture_confirmed = (
        expected not in {"", "auto"}
        and blocking_warn is None
        and structure.get("structure_ok", False)
    )
    ok_for_drive = capture_confirmed and not body_false_positive

    return {
        "expected_ide": expected or None,
        "capture_confirmed": capture_confirmed,
        "ok_for_drive": ok_for_drive,
        "window_titles": titles,
        "ide_window_warning": warn,
        "vision_deferred_window_mismatch": vision_deferred,
        "body_ide_mentions": body,
        "body_false_positive": body_false_positive,
        "chat_composer_candidates": chat,
        "nl": nl,
        "structure": structure,
        "reasons": reasons,
    }


def validate_vql_sidecar_file(path: str) -> dict[str, Any]:
    """Load a ``.png.vql.json`` sidecar and return ``capture_validation`` (recompute if missing)."""
    import json
    from pathlib import Path

    data = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    metadata = data.get("metadata") or {}
    existing = metadata.get("capture_validation")
    if isinstance(existing, dict) and existing.get("structure"):
        return existing
    render = metadata.get("render_intent") or {}
    layers = render.get("layers") or data.get("layers") or []
    ide = str(existing.get("expected_ide") if isinstance(existing, dict) else "") or expected_ide_from_env()
    nl = str(metadata.get("describe", {}).get("nl") or render.get("nl") or "")
    return validate_vql_capture(layers=layers, ide=ide, reverse=render, nl=nl or None)


__all__ = [
    "body_ide_mentions",
    "chat_composer_candidates",
    "expected_ide_from_env",
    "ide_window_warning",
    "validate_vql_capture",
    "validate_vql_sidecar_file",
    "validate_vql_structure",
    "window_titles_from_layers",
]
