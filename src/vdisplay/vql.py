"""Reading VQL sidecars: what is on the screen, according to the files on disk.

Extracted from ``koru/src/koru/integrations/vdisplay_client.py`` on 2026-07-22
(koru boundary proposal §1). Sidecar shape is vdisplay's own contract, so
parsing it belongs here rather than in a consumer — vdisplay already owned
half of it through :func:`vdisplay.integrations.normalize_vql_ui_elements`
and :func:`vdisplay.integrations.build_imgl_layers`, which the functions
below call.

What deliberately stayed in koru: everything that decides whether a sidecar
is *fresh enough to act on*. Staleness thresholds, autonomy-session
directories and candidate ordering are policy about a run, not facts about a
screen. koru keeps ``load_vql_metadata``, ``_vql_candidate_is_stale`` and
``_vql_imgl_fallback_layers`` for that reason.

Every function here is pure with respect to koru: given a path or a parsed
dict it reads files and returns data, and imports nothing from koru.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

__all__ = [
    "png_path_for_vql_sidecar",
    "main_vql_layer_count",
    "imgl_sidecar_path_for_vql",
    "layers_from_imgl_sidecar_file",
    "layers_from_vdisplay_sidecar",
    "with_embedded_capture_validation",
    "vql_from_ui_elements",
    "vql_from_fresh_elements",
    "vql_from_sidecar_layers",
    "vql_from_program_wrapper",
    "vql_from_screen_context",
    "vql_metadata_default",
    "parse_fresh_vql_elements",
]


def png_path_for_vql_sidecar(vql_path: str) -> Path | None:
    """Return the capture PNG a ``*.png.vql.json`` sidecar describes, if it exists."""
    if vql_path.endswith(".png.vql.json"):
        png = vql_path[: -len(".vql.json")]
        return Path(png) if os.path.isfile(png) else None
    return None


def main_vql_layer_count(vql_path: str | Path) -> int:
    """Count normalized layers in a sidecar; 0 when missing or unreadable."""
    path = Path(vql_path)
    if not path.is_file():
        return 0
    try:
        with open(path) as f:
            data = json.load(f)
    except Exception:
        return 0
    return len(layers_from_vdisplay_sidecar(data))


def imgl_sidecar_path_for_vql(vql_path: str) -> str | None:
    """Return the sibling ``*.vql.imgl.json`` path when one exists on disk."""
    if not vql_path.endswith(".vql.json"):
        return None
    alt = vql_path[: -len(".vql.json")] + ".vql.imgl.json"
    return alt if os.path.isfile(alt) else None


def layers_from_imgl_sidecar_file(vql_path: str) -> tuple[list[dict], str | None]:
    """Load actuation layers from sibling ``.vql.imgl.json`` when main VQL sidecar is empty."""
    imgl_path = imgl_sidecar_path_for_vql(vql_path)
    if not imgl_path:
        return [], None
    png_path = png_path_for_vql_sidecar(vql_path)
    if png_path is not None:
        try:
            if os.path.getmtime(imgl_path) + 1 < os.path.getmtime(png_path):
                return [], None
        except OSError:
            pass
    try:
        with open(imgl_path) as f:
            imgl_data = json.load(f)
    except Exception:
        return [], None
    try:
        from vdisplay.integrations import build_imgl_layers

        built = build_imgl_layers({"ok": True, "scene": imgl_data})
    except Exception:
        built = []
    if not built:
        return [], None
    return (
        layers_from_vdisplay_sidecar(
            {"layers": built, "metadata": {"render_intent": {"layers": built}}}
        ),
        imgl_path,
    )


def layers_from_vdisplay_sidecar(data: dict) -> list[dict]:
    """Normalize sidecar elements through the canonical vdisplay normalizer."""
    from vdisplay.integrations import normalize_vql_ui_elements

    return normalize_vql_ui_elements(data)


def with_embedded_capture_validation(meta: dict, raw: dict | None = None) -> dict:
    """Lift a nested ``capture_validation`` block to the top level, if present."""
    if meta.get("capture_validation"):
        return meta
    nested = raw.get("metadata") if isinstance(raw, dict) and isinstance(raw.get("metadata"), dict) else {}
    cv = meta.get("metadata", {}).get("capture_validation") if isinstance(meta.get("metadata"), dict) else None
    if cv is None and isinstance(nested, dict):
        cv = nested.get("capture_validation")
    if isinstance(cv, dict):
        meta["capture_validation"] = cv
    return meta


def vql_from_ui_elements(data: dict, cand: str, png_path: Path | None) -> dict:
    """Normalize a sidecar that already carries ui_elements (analysis-style VQL)."""
    data["_source"] = cand
    if png_path and png_path.is_file():
        data["_png"] = str(png_path)
        data["_freshness"] = {"age_s": round(time.time() - png_path.stat().st_mtime, 2)}
    if "layers" not in data:
        data["layers"] = data["ui_elements"]
    return with_embedded_capture_validation(data, data)


def vql_from_fresh_elements(data: dict, cand: str, png_path: Path | None) -> dict:
    """Normalize a fresh-capture sidecar carrying raw elements."""
    res = parse_fresh_vql_elements(data, cand)
    if png_path and png_path.is_file():
        res["_png"] = str(png_path)
    return with_embedded_capture_validation(res, data)


def vql_from_sidecar_layers(
    data: dict, cand: str, sidecar_layers: list[dict], png_path: Path | None
) -> dict:
    """Normalize vdisplay/imgl sidecar layers into the metadata dict shape."""
    out = {
        "ui_elements": sidecar_layers,
        "layers": sidecar_layers,
        "metadata": data.get("metadata") or {},
        "environment": (data.get("metadata") or {}).get("environment") or data.get("environment") or {},
        "_source": cand,
    }
    if png_path and png_path.is_file():
        out["_png"] = str(png_path)
    return with_embedded_capture_validation(out, data)


def vql_from_program_wrapper(data: dict, cand: str) -> dict | None:
    """Unwrap a nested vql.program dict when present; None to keep dispatching."""
    if "vql" in data and isinstance(data.get("vql"), dict):
        prog = data["vql"].get("program", data["vql"])
        if isinstance(prog, dict):
            prog["_source"] = cand
            if "layers" not in prog and "ui_elements" in prog:
                prog["layers"] = prog["ui_elements"]
            return prog
    return None


def vql_from_screen_context(data: dict, cand: str) -> dict:
    """Normalize a screen_context/metadata-only sidecar into the metadata dict shape."""
    meta = data.get("metadata") or data.get("screen_context") or {}
    layers = layers_from_vdisplay_sidecar({"metadata": meta})
    return with_embedded_capture_validation(
        {
            "ui_elements": layers,
            "layers": layers,
            "metadata": meta,
            "environment": meta.get("environment") or data.get("environment") or {},
            "_source": cand,
        },
        data,
    )


def vql_metadata_default(data: dict, cand: str) -> dict:
    """Fallback normalization: tag source and mirror ui_elements into layers."""
    if isinstance(data.get("program"), (str, dict)) and "elements" not in data:
        data["_source"] = cand
        if "layers" not in data:
            data["layers"] = data.get("ui_elements", [])
        return data
    data["_source"] = cand
    if "layers" not in data:
        data["layers"] = data.get("ui_elements", [])
    return data


def parse_fresh_vql_elements(data: dict, cand: str) -> dict:
    """Normalize fresh elements, preserving the caller's provenance fields."""
    from vdisplay.integrations import normalize_vql_ui_elements

    ui_elements = normalize_vql_ui_elements(data, fallback_center=(1024, 640))
    for raw, element in zip(data["elements"], ui_elements, strict=False):
        element["click_center"]["note"] = (
            f"fresh VQL elem, color={raw.get('color')}, conf={raw.get('confidence')}"
        )
    return {
        "ui_elements": ui_elements,
        "layers": ui_elements,
        "element_count": data.get("element_count", len(ui_elements)),
        "by_role": data.get("by_role", {}),
        "scene": data.get("scene"),
        "_source": cand,
        "raw_fresh": True,
    }
