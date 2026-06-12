"""Export ScreenContext to VQL metadata and vector render artifacts."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from ..application.env_defaults import env_flag
from .imgl_bridge import imgl_available
from .screen_context import ScreenContext
from .vql_capture_validation import expected_ide_from_env, validate_vql_capture
from ..application.config_options import get_runtime_options


def vql_enabled() -> bool:
    return env_flag("VDISPLAY_VQL", default=True)


def vql_available() -> bool:
    if not vql_enabled():
        return False
    try:
        import vql  # noqa: F401

        return True
    except ImportError:
        return False


def _capture_block(ctx: ScreenContext) -> dict[str, Any]:
    capture = dict(ctx.capture)
    path = Path(ctx.image_path).expanduser()
    if path.is_file():
        capture.setdefault("path", str(path.resolve()))
    capture.setdefault("width", capture.get("width"))
    capture.setdefault("height", capture.get("height"))
    capture.setdefault("source", capture.get("source") or "vdisplay")
    capture.setdefault("fingerprint", ctx.fingerprint)
    return capture


def _environment_block(ctx: ScreenContext) -> dict[str, Any]:
    block = dict(ctx.environment)
    block.setdefault("observed_at", ctx.observed_at)
    routing = block.get("routing")
    if isinstance(routing, dict) and routing.get("application_profile"):
        block["application_profile"] = routing["application_profile"]
    return block


def _try_from_screen_context(ctx: ScreenContext) -> dict[str, Any] | None:
    try:
        from img2vql.vdisplay_context import from_screen_context

        program = from_screen_context(ctx.to_dict())
        if not hasattr(program, "to_dict"):
            return None
        payload = program.to_dict()
        # Only use this result if it has meaningful layers/elements
        scene_layers = payload.get("scene", {}).get("layers") or []
        top_elements = payload.get("elements") or []
        if not scene_layers and not top_elements:
            return None  # Fall through to _try_imgl_scene / _try_adopt_screenshot
        metadata = dict(payload.get("metadata") or {})
        metadata["render_intent"] = _enrich_render_intent(
            ctx,
            dict(metadata.get("render_intent") or {}),
        )
        payload["metadata"] = metadata
        return payload
    except ImportError:
        return None
    except Exception:
        return None


def _try_imgl_scene(ctx: ScreenContext) -> dict[str, Any] | None:
    """Build VQL program from imgl scene with full actuation layers."""
    if not ctx.imgl.get("ok") or not imgl_available():
        return None
    capture = ctx.capture
    width = int(capture.get("width") or 0)
    height = int(capture.get("height") or 0)
    layers = _build_imgl_layers(ctx.imgl)
    if not layers:
        return None
    return {
        "version": "1.0",
        "scene": {"width": width, "height": height, "layers": layers, "elements": layers},
        "layers": layers,
        "elements": layers,
        "metadata": {
            "source": "imgl",
            "element_count": ctx.imgl.get("element_count") or len(layers),
            "window_count": ctx.imgl.get("window_count") or 0,
        },
    }


def _adopted_element_to_layer(el: dict[str, Any]) -> dict[str, Any] | None:
    """Convert a single adopted element dict to a VQL layer dict."""
    bbox = el.get("bbox")
    if not isinstance(bbox, (list, tuple)) or len(bbox) < 4:
        return None
    x, y, w, h = bbox[0], bbox[1], bbox[2], bbox[3]
    bbox_dict = {"x": x, "y": y, "w": w, "h": h}
    center = {"x": x + w // 2, "y": y + h // 2}
    return {
        "kind": str(el.get("role") or "element"),
        "id": str(el.get("id") or ""),
        "text": el.get("label") or el.get("text") or "",
        "bbox": bbox_dict,
        "center": center,
        "click_center": center,
        "confidence": float(el.get("confidence") or 0.0) or None,
        "metadata": {"source": "img2vql-adopt", "location": el.get("location")},
    }


def _adopted_elements_to_layers(elements: list[Any]) -> list[dict[str, Any]]:
    """Convert adopted element list to VQL layer list."""
    layers: list[dict[str, Any]] = []
    for el in elements:
        if not isinstance(el, dict):
            continue
        layer = _adopted_element_to_layer(el)
        if layer:
            layers.append(layer)
    return layers


def _try_adopt_screenshot(ctx: ScreenContext) -> dict[str, Any] | None:
    """Use img2vql.adopt_screenshot for top-level elements (bboxes, click_centers)."""
    if not ctx.image_path or not Path(ctx.image_path).is_file():
        return None
    try:
        from img2vql import adopt_screenshot

        adopted = adopt_screenshot(ctx.image_path)
        if not isinstance(adopted, dict) or not adopted.get("ok"):
            return None
        elements = adopted.get("elements") or []
        if not elements:
            return None
        capture = ctx.capture
        width = int(capture.get("width") or 0)
        height = int(capture.get("height") or 0)
        layers = _adopted_elements_to_layers(elements)
        return {
            "version": "1.0",
            "scene": {"width": width, "height": height, "layers": layers, "elements": elements},
            "layers": layers,
            "elements": elements,
            "metadata": {
                "source": "img2vql",
                "element_count": adopted.get("element_count") or len(elements),
                "describe": {"nl": adopted.get("description") or ""},
            },
        }
    except ImportError:
        pass
    except Exception:
        pass
    return None


def _fallback_program(ctx: ScreenContext) -> dict[str, Any]:
    return {
        "version": "1.0",
        "scene": {"width": ctx.capture.get("width", 0), "height": ctx.capture.get("height", 0)},
        "layers": [],
        "relations": [],
        "metadata": {},
    }


def _assemble_metadata(ctx: ScreenContext, program: dict[str, Any]) -> dict[str, Any]:
    metadata = dict(program.get("metadata") or {})
    metadata["capture"] = _capture_block(ctx)
    metadata["environment"] = _environment_block(ctx)
    if ctx.map_pack:
        metadata["gui_map"] = ctx.map_pack
    if ctx.verify:
        metadata["verify"] = ctx.verify
    if ctx.vision:
        metadata["vision"] = ctx.vision
    if ctx.nl:
        metadata.setdefault("describe", {})["nl"] = ctx.nl
    metadata["render_intent"] = reverse_generation_descriptor(ctx)
    return metadata


def _try_merge_metadata(ctx: ScreenContext, metadata: dict[str, Any]) -> dict[str, Any]:
    if not vql_available() or not ctx.image_path:
        return metadata
    try:
        from img2vql.metadata import merge_program_metadata

        metadata.update(merge_program_metadata(metadata, ctx.image_path))
    except ImportError:
        pass
    except Exception:
        pass
    return metadata


def _try_validate_metadata(program: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    if not vql_available():
        return metadata
    try:
        from vql import validate_program_metadata

        issues = validate_program_metadata(program.get("metadata") or {})
        if issues:
            metadata["validation_issues"] = [
                issue.to_dict() if hasattr(issue, "to_dict") else str(issue)
                for issue in issues
            ]
    except Exception:
        pass
    return metadata


def _first_nonempty_layer_list(*values: Any) -> list[dict[str, Any]]:
    for value in values:
        if not isinstance(value, list):
            continue
        layers = [item for item in value if isinstance(item, dict)]
        if layers:
            return layers
    return []


def _layers_for_capture_validation(
    *,
    program: dict[str, Any] | None,
    render: dict[str, Any],
) -> list[dict[str, Any]]:
    program = program or {}
    scene = program.get("scene") if isinstance(program.get("scene"), dict) else {}
    return _first_nonempty_layer_list(
        render.get("layers"),
        program.get("layers"),
        scene.get("layers"),
        program.get("elements"),
        scene.get("elements"),
        render.get("ui_elements"),
    )


def _layers_to_ui_elements(layers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": layer.get("id"),
            "role": layer.get("kind") or layer.get("role"),
            "label": layer.get("text") or layer.get("label"),
            "bounds": layer.get("bbox") or layer.get("bounds"),
            "click_center": layer.get("click_center") or layer.get("center"),
        }
        for layer in layers
        if isinstance(layer, dict)
    ]


def _attach_capture_validation(
    metadata: dict[str, Any],
    *,
    program: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Embed IDE/structure validation for autonomy observe → decide → act."""
    render = dict(metadata.get("render_intent") or {})
    layers = _layers_for_capture_validation(program=program, render=render)
    if layers and not render.get("layers"):
        render["layers"] = layers
    if layers and not render.get("ui_elements"):
        render["ui_elements"] = _layers_to_ui_elements(layers)
    ide = expected_ide_from_env()
    nl = str(metadata.get("describe", {}).get("nl") or render.get("nl") or "")
    validation = validate_vql_capture(layers=layers, ide=ide, reverse=render, nl=nl or None)
    metadata["capture_validation"] = validation
    render["capture_validation"] = validation
    metadata["render_intent"] = render
    return metadata


def context_to_vql_program(ctx: ScreenContext) -> dict[str, Any]:
    """Build or merge a VQLProgram-compatible dict from ScreenContext."""
    program = _try_from_screen_context(ctx)
    if program is not None:
        metadata = dict(program.get("metadata") or {})
        metadata["capture"] = _capture_block(ctx)
        metadata["environment"] = _environment_block(ctx)
        if ctx.map_pack:
            metadata["gui_map"] = ctx.map_pack
        if ctx.verify:
            metadata["verify"] = ctx.verify
        if ctx.vision:
            metadata["vision"] = ctx.vision
        if ctx.nl:
            metadata.setdefault("describe", {})["nl"] = ctx.nl
        metadata["render_intent"] = _enrich_render_intent(
            ctx,
            dict(metadata.get("render_intent") or {}),
        )
        metadata = _attach_capture_validation(metadata, program=program)
        program["metadata"] = metadata
        return program

    program = _try_imgl_scene(ctx)
    if program is None:
        program = _try_adopt_screenshot(ctx)
    if program is None:
        program = _fallback_program(ctx)

    metadata = _assemble_metadata(ctx, program)
    metadata = _try_merge_metadata(ctx, metadata)
    metadata = _try_validate_metadata(program, metadata)
    metadata = _attach_capture_validation(metadata, program=program)
    program["metadata"] = metadata
    return program


def reverse_generation_descriptor(ctx: ScreenContext) -> dict[str, Any]:
    """Structured hints for layout/SVG regeneration from metadata (not pixels)."""
    base: dict[str, Any] | None = None
    try:
        from img2vql.vdisplay_context import reverse_generate
        from vql.schema.program import VQLProgram

        capture = ctx.capture
        program = VQLProgram.from_dict(
            {
                "version": "1.0",
                "scene": {
                    "width": int(capture.get("width") or 0),
                    "height": int(capture.get("height") or 0),
                },
                "layers": [],
                "relations": [],
                "metadata": {
                    "nl": ctx.nl,
                    "capture": _capture_block(ctx),
                    "environment": _environment_block(ctx),
                },
            }
        )
        base = reverse_generate(program)
    except ImportError:
        base = None
    except Exception:
        base = None

    if base is None:
        capture = ctx.capture
        width = int(capture.get("width") or 0)
        height = int(capture.get("height") or 0)
        base = {
            "mode": "layout_reconstruction",
            "canvas": {"width": width, "height": height},
            "nl": ctx.nl,
            "layers": [],
            "prompt_block": ctx.nl or f"UI screenshot {width}x{height}",
        }

    return _enrich_render_intent(ctx, base)


def _resolve_canvas_size(
    capture: dict[str, Any],
    descriptor: dict[str, Any],
) -> tuple[int, int]:
    width = int(capture.get("width") or descriptor.get("canvas", {}).get("width") or 0)
    height = int(capture.get("height") or descriptor.get("canvas", {}).get("height") or 0)
    return width, height


def _resolve_scene_class(imgl: dict[str, Any]) -> str:
    img2nl = imgl.get("img2nl") or {}
    if isinstance(img2nl, dict):
        return str(img2nl.get("scene_class") or "")
    return ""


def _bbox_center(bbox: dict[str, Any] | None) -> dict[str, int] | None:
    try:
        from imgl.export.actuation_layers import bbox_center

        return bbox_center(bbox)
    except ImportError:
        pass
    if not isinstance(bbox, dict):
        return None
    x = int(bbox.get("x") or 0)
    y = int(bbox.get("y") or 0)
    w = int(bbox.get("w") or bbox.get("width") or 0)
    h = int(bbox.get("h") or bbox.get("height") or 0)
    if w <= 0 or h <= 0:
        return None
    return {"x": x + w // 2, "y": y + h // 2}


def _layer_from_bbox(
    *,
    kind: str,
    layer_id: str | None = None,
    text: str | None = None,
    bbox: dict[str, Any] | None = None,
    confidence: float | None = None,
) -> dict[str, Any] | None:
    try:
        from imgl.export.actuation_layers import layer_from_bbox

        return layer_from_bbox(
            kind=kind,
            layer_id=layer_id,
            text=text,
            bbox=bbox,
            confidence=confidence,
        )
    except ImportError:
        pass
    if not isinstance(bbox, dict):
        return None
    center = _bbox_center(bbox)
    if center is None:
        return None
    layer: dict[str, Any] = {
        "kind": kind,
        "id": layer_id,
        "text": text,
        "bbox": bbox,
        "center": center,
        "click_center": center,
    }
    if confidence is not None:
        layer["confidence"] = confidence
    return layer


def _normalize_imgl_scene_payload(raw: Any) -> dict[str, Any] | None:
    """Parse IMGL scene payloads that may be dicts or JSON strings (vdisplay_context cache)."""
    import json

    data: dict[str, Any] | None
    if isinstance(raw, dict):
        data = raw
    elif isinstance(raw, str):
        try:
            loaded = json.loads(raw)
        except json.JSONDecodeError:
            return None
        data = loaded if isinstance(loaded, dict) else None
    else:
        return None
    if not data:
        return None
    if data.get("windows") or data.get("elements") or data.get("ocr_boxes"):
        return data
    nested = data.get("scene")
    if isinstance(nested, dict):
        merged = dict(nested)
        for key in ("windows", "elements", "ocr_boxes", "orphan_elements"):
            if key in data and key not in merged:
                merged[key] = data[key]
        return merged
    return data


def _extract_imgl_scene(imgl: dict[str, Any]) -> dict[str, Any] | None:
    """Normalize scene dict from ctx.imgl (analyze_with_imgl or img2nl describe path)."""
    if not isinstance(imgl, dict):
        return None
    if imgl.get("ok") and imgl.get("scene") is not None:
        scene = _normalize_imgl_scene_payload(imgl["scene"])
        if scene is not None:
            return scene
    img2nl = imgl.get("img2nl")
    if isinstance(img2nl, dict) and img2nl.get("ok"):
        meta = img2nl.get("metadata") or {}
        if isinstance(meta, dict) and meta.get("scene") is not None:
            scene = _normalize_imgl_scene_payload(meta["scene"])
            if scene is not None:
                return scene
    return None


def _element_layer_from_dict(element: dict[str, Any]) -> dict[str, Any] | None:
    """Build a layer dict from an element dict (handles type/role fallbacks)."""
    kind = str(element.get("type") or element.get("role") or "element")
    return _layer_from_bbox(
        kind=kind,
        layer_id=str(element.get("id") or ""),
        text=element.get("text"),
        bbox=element.get("bbox"),
        confidence=float(element.get("confidence") or 0.0) or None,
    )


def _ocr_layer_from_dict(ocr: dict[str, Any]) -> dict[str, Any] | None:
    """Build an OCR layer dict from an ocr_box dict."""
    text = str(ocr.get("text") or "").strip()
    if not text:
        return None
    return _layer_from_bbox(
        kind="ocr",
        text=text,
        bbox=ocr.get("bbox"),
        confidence=float(ocr.get("confidence") or 0.0) or None,
    )


def _extend_element_layers(
    layers: list[dict[str, Any]],
    elements: list[Any],
) -> None:
    """Append valid element layers from an iterable to the layers list."""
    for element in elements:
        if not isinstance(element, dict):
            continue
        item = _element_layer_from_dict(element)
        if item:
            layers.append(item)


def _build_imgl_layers(imgl: dict[str, Any]) -> list[dict[str, Any]]:
    """Build actuation layers from imgl scene data (windows+elements+ocr)."""
    limit = get_runtime_options().vql.layer_export_limit
    scene = _extract_imgl_scene(imgl)
    if not isinstance(scene, dict):
        return []
    layers: list[dict[str, Any]] = []
    for window in scene.get("windows") or []:
        if not isinstance(window, dict):
            continue
        window_layer = _layer_from_bbox(
            kind="window",
            layer_id=str(window.get("id") or ""),
            text=window.get("title"),
            bbox=window.get("bbox"),
        )
        if window_layer:
            layers.append(window_layer)
        _extend_element_layers(layers, window.get("elements") or [])
    _extend_element_layers(layers, scene.get("elements") or [])
    _extend_element_layers(layers, scene.get("orphan_elements") or [])
    for ocr in scene.get("ocr_boxes") or []:
        if not isinstance(ocr, dict):
            continue
        item = _ocr_layer_from_dict(ocr)
        if item:
            layers.append(item)
    return layers[:limit]


def _warn_empty_vql_layers(ctx: ScreenContext, program: dict[str, Any]) -> None:
    """Warn when photo-VQL sidecar would have no click targets (missing imgl or empty scene)."""
    import warnings

    from .imgl_bridge import imgl_available, imgl_enabled

    render = (program.get("metadata") or {}).get("render_intent") or {}
    layers = _layers_for_capture_validation(program=program, render=render)
    if layers:
        return
    if not imgl_enabled():
        return
    if not imgl_available():
        warnings.warn(
            "VDISPLAY_IMGL=1 but imgl is not installed — VQL sidecar will have empty layers. "
            "Install: pip install -e \".[observe]\" (requires system tesseract-ocr)",
            stacklevel=2,
        )
        return
    if _extract_imgl_scene(ctx.imgl) is None and not ctx.imgl.get("ok"):
        warnings.warn(
            "imgl installed but scene analysis failed or was skipped — VQL layers empty. "
            f"imgl error={ctx.imgl.get('error') or 'unknown'}",
            stacklevel=2,
        )
        return
    warnings.warn(
        "imgl scene produced zero actuation layers — photo VQL mouse targets unavailable",
        stacklevel=2,
    )


def _maybe_add_map_targets(
    enriched: dict[str, Any],
    map_pack: dict[str, Any] | None,
) -> None:
    if not map_pack or "map_targets" in enriched:
        return
    elements = map_pack.get("elements") or {}
    if isinstance(elements, dict):
        enriched["map_targets"] = [
            {"id": key, "label": (value or {}).get("label"), "role": (value or {}).get("role")}
            for key, value in elements.items()
            if isinstance(value, dict)
        ][: get_runtime_options().vql.map_target_limit]


def _maybe_add_routing_hint(
    enriched: dict[str, Any],
    environment: dict[str, Any],
) -> None:
    routing = environment.get("routing")
    if isinstance(routing, dict) and "routing_hint" not in enriched:
        enriched["routing_hint"] = {
            "provider": routing.get("selected_provider"),
            "profile": routing.get("application_profile"),
        }


def _enrich_render_intent(ctx: ScreenContext, descriptor: dict[str, Any]) -> dict[str, Any]:
    """Add vdisplay-specific scene/map hints on top of img2vql reverse_generate output."""
    enriched = dict(descriptor)
    width, height = _resolve_canvas_size(ctx.capture, enriched)
    enriched.setdefault("mode", "layout_reconstruction")
    enriched.setdefault("canvas", {"width": width, "height": height})
    enriched.setdefault("nl", ctx.nl)
    enriched.setdefault("prompt_block", ctx.nl or f"UI screenshot {width}x{height}")
    enriched.setdefault("scene_class", _resolve_scene_class(ctx.imgl) or "ui_screenshot")

    if not enriched.get("layers"):
        enriched["layers"] = _build_imgl_layers(ctx.imgl)

    if enriched.get("layers") and not enriched.get("ui_elements"):
        enriched["ui_elements"] = _layers_to_ui_elements(enriched["layers"])

    _maybe_add_map_targets(enriched, ctx.map_pack)
    _maybe_add_routing_hint(enriched, ctx.environment)
    return enriched


def write_vql_artifacts(
    ctx: ScreenContext,
    *,
    vql_path: str | Path | None = None,
    svg_path: str | Path | None = None,
) -> dict[str, str]:
    """Persist VQL JSON and optional SVG derived from context."""
    program = context_to_vql_program(ctx)
    ctx.vql["program"] = program
    reverse = reverse_generation_descriptor(ctx)
    validation = (program.get("metadata") or {}).get("capture_validation")
    if isinstance(validation, dict):
        reverse["capture_validation"] = validation
        ctx.vql["capture_validation"] = validation
    ctx.vql["reverse"] = reverse
    _warn_empty_vql_layers(ctx, program)

    written: dict[str, str] = {}
    image = Path(ctx.image_path).expanduser()
    default_vql = image.with_suffix(image.suffix + ".vql.json")
    out_vql = Path(vql_path).expanduser() if vql_path else default_vql
    out_vql.parent.mkdir(parents=True, exist_ok=True)
    out_vql.write_text(json.dumps(program, indent=2, ensure_ascii=False), encoding="utf-8")
    written["vql"] = str(out_vql.resolve())
    ctx.artifacts["vql"] = written["vql"]

    if svg_path is not None and vql_available():
        out_svg = Path(svg_path).expanduser()
        out_svg.parent.mkdir(parents=True, exist_ok=True)
        try:
            from vql import VQLProgram, render_to_svg

            vql_program = VQLProgram.from_dict(program)
            svg_text = render_to_svg(vql_program)
            out_svg.write_text(svg_text, encoding="utf-8")
            written["svg"] = str(out_svg.resolve())
            ctx.artifacts["svg"] = written["svg"]
        except Exception as exc:
            ctx.vql["svg_error"] = str(exc)

    return written
