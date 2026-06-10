"""Export ScreenContext to VQL metadata and vector render artifacts."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

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


def context_to_vql_program(ctx: ScreenContext) -> dict[str, Any]:
    """Build or merge a VQLProgram-compatible dict from ScreenContext."""
    try:
        from img2vql.vdisplay_context import from_screen_context

        program = from_screen_context(ctx.to_dict())
        if hasattr(program, "to_dict"):
            payload = program.to_dict()
            metadata = dict(payload.get("metadata") or {})
            metadata["render_intent"] = _enrich_render_intent(
                ctx,
                dict(metadata.get("render_intent") or {}),
            )
            payload["metadata"] = metadata
            return payload
    except ImportError:
        pass
    except Exception:
        pass

    program: dict[str, Any] | None = None

    imgl_scene = (ctx.imgl.get("scene") if ctx.imgl.get("ok") else None)
    if imgl_scene and imgl_available():
        try:
            from imgl.export.vql_adapter import scene_to_vql
            from imgl.types import Scene

            scene = Scene.from_dict(imgl_scene) if hasattr(Scene, "from_dict") else None
            if scene is not None:
                program = scene_to_vql(scene)
        except Exception:
            program = None

    if program is None and ctx.image_path and Path(ctx.image_path).is_file():
        try:
            from img2vql import adopt_screenshot

            adopted = adopt_screenshot(ctx.image_path)
            if isinstance(adopted, dict):
                program = adopted
            elif hasattr(adopted, "to_dict"):
                program = adopted.to_dict()
        except ImportError:
            pass
        except Exception:
            program = None

    if program is None:
        program = {
            "version": "1.0",
            "scene": {"width": ctx.capture.get("width", 0), "height": ctx.capture.get("height", 0)},
            "layers": [],
            "relations": [],
            "metadata": {},
        }

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
    program["metadata"] = metadata

    if vql_available():
        try:
            from img2vql.metadata import merge_program_metadata

            if ctx.image_path:
                metadata.update(merge_program_metadata(metadata, ctx.image_path))
                program["metadata"] = metadata
        except ImportError:
            pass
        except Exception:
            pass

        try:
            from vql import validate_program_metadata

            issues = validate_program_metadata(program.get("metadata") or {})
            if issues:
                metadata["validation_issues"] = [issue.to_dict() if hasattr(issue, "to_dict") else str(issue) for issue in issues]
                program["metadata"] = metadata
        except Exception:
            pass

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


def _enrich_render_intent(ctx: ScreenContext, descriptor: dict[str, Any]) -> dict[str, Any]:
    """Add vdisplay-specific scene/map hints on top of img2vql reverse_generate output."""
    enriched = dict(descriptor)
    capture = ctx.capture
    width = int(capture.get("width") or enriched.get("canvas", {}).get("width") or 0)
    height = int(capture.get("height") or enriched.get("canvas", {}).get("height") or 0)
    enriched.setdefault("mode", "layout_reconstruction")
    enriched.setdefault("canvas", {"width": width, "height": height})
    enriched.setdefault("nl", ctx.nl)
    enriched.setdefault("prompt_block", ctx.nl or f"UI screenshot {width}x{height}")

    scene_class = ""
    img2nl = ctx.imgl.get("img2nl") or {}
    if isinstance(img2nl, dict):
        scene_class = str(img2nl.get("scene_class") or "")
    enriched.setdefault("scene_class", scene_class or "ui_screenshot")

    if not enriched.get("layers"):
        layers: list[dict[str, Any]] = []
        imgl_scene = ctx.imgl.get("scene") if ctx.imgl.get("ok") else None
        if isinstance(imgl_scene, dict):
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
        enriched["layers"] = layers

    if ctx.map_pack and "map_targets" not in enriched:
        elements = ctx.map_pack.get("elements") or {}
        if isinstance(elements, dict):
            enriched["map_targets"] = [
                {"id": key, "label": (value or {}).get("label"), "role": (value or {}).get("role")}
                for key, value in elements.items()
                if isinstance(value, dict)
            ][:32]

    routing = ctx.environment.get("routing")
    if isinstance(routing, dict) and "routing_hint" not in enriched:
        enriched["routing_hint"] = {
            "provider": routing.get("selected_provider"),
            "profile": routing.get("application_profile"),
        }

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
