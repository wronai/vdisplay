"""Export ScreenContext to VQL metadata and vector render artifacts."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .imgl_bridge import imgl_available
from .screen_context import ScreenContext


def vql_enabled() -> bool:
    flag = os.environ.get("VDISPLAY_VQL", "1").strip().lower()
    return flag not in {"0", "false", "no", "off"}


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
    imgl_scene = (ctx.imgl.get("scene") if ctx.imgl.get("ok") else None)
    if not imgl_scene or not imgl_available():
        return None
    try:
        from imgl.export.vql_adapter import scene_to_vql
        from imgl.types import Scene

        scene = Scene.from_dict(imgl_scene) if hasattr(Scene, "from_dict") else None
        if scene is not None:
            return scene_to_vql(scene)
    except Exception:
        pass
    return None


def _try_adopt_screenshot(ctx: ScreenContext) -> dict[str, Any] | None:
    if not ctx.image_path or not Path(ctx.image_path).is_file():
        return None
    try:
        from img2vql import adopt_screenshot

        adopted = adopt_screenshot(ctx.image_path)
        if isinstance(adopted, dict):
            return adopted
        if hasattr(adopted, "to_dict"):
            return adopted.to_dict()
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


def context_to_vql_program(ctx: ScreenContext) -> dict[str, Any]:
    """Build or merge a VQLProgram-compatible dict from ScreenContext."""
    program = _try_from_screen_context(ctx)
    if program is not None:
        return program

    program = _try_imgl_scene(ctx)
    if program is None:
        program = _try_adopt_screenshot(ctx)
    if program is None:
        program = _fallback_program(ctx)

    metadata = _assemble_metadata(ctx, program)
    metadata = _try_merge_metadata(ctx, metadata)
    metadata = _try_validate_metadata(program, metadata)
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


def _build_imgl_layers(imgl: dict[str, Any]) -> list[dict[str, Any]]:
    layers: list[dict[str, Any]] = []
    imgl_scene = imgl.get("scene") if imgl.get("ok") else None
    if not isinstance(imgl_scene, dict):
        return layers
    for window in imgl_scene.get("windows") or []:
        layers.append(
            {
                "kind": "window",
                "id": window.get("id"),
                "title": window.get("title"),
                "bbox": window.get("bbox"),
            }
        )
    for element in imgl_scene.get("elements") or []:
        layers.append(
            {
                "kind": element.get("role") or "element",
                "text": element.get("text"),
                "bbox": element.get("bbox"),
            }
        )
    return layers


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
        ][:32]


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
    ctx.vql["reverse"] = reverse_generation_descriptor(ctx)

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
