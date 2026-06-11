"""Observe screen — unified capture + IMGL + VQL metadata export."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..application.config_options import get_runtime_options
from ..application.commands import CommandRequest, CommandVerb
from ..application.executor import execute
from ..integrations.pipeline import observe_screen
from ..integrations.vql_bridge import context_to_vql_program, reverse_generation_descriptor
from .io import print_json


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser(
        "observe",
        help="Capture screen and build reusable ScreenContext (IMGL/VQL metadata)",
    )
    parser.add_argument("--output", "-o", help="Screenshot PNG path (default: ./observe.png)")
    parser.add_argument("--display", help="DISPLAY / monitor context")
    parser.add_argument("--map", dest="map_path", help="Attach GUI map pack for scope metadata")
    parser.add_argument("--vql", dest="vql_path", help="Write VQL program JSON")
    parser.add_argument("--svg", dest="svg_path", help="Render layout SVG from VQL program")
    opts = get_runtime_options()
    parser.add_argument("--format", choices=tuple(opts.observe_output_formats), default="json")
    parser.add_argument("--no-imgl", action="store_true", help="Skip IMGL scene analysis")
    parser.add_argument("--no-vql", action="store_true", help="Skip VQL export")
    parser.add_argument("--no-sidecar", action="store_true", help="Do not write .context.json sidecar")
    parser.set_defaults(func=handle_observe)


def handle_observe(args: argparse.Namespace) -> int:
    output = Path(args.output or "observe.png").expanduser()
    if not output.is_absolute():
        output = Path.cwd() / output

    shot = execute(
        CommandRequest(
            verb=CommandVerb.SCREENSHOT,
            output=str(output),
            display=args.display,
            extra={"skip_img2nl": True},
        )
    )
    if not shot.ok:
        print_json({"ok": False, "error": shot.error.to_dict() if shot.error else "screenshot failed"})
        return 1

    image_path = shot.data.get("path") or str(output)
    ctx = observe_screen(
        image_path=image_path,
        capture_meta=shot.data,
        diagnostics=shot.diagnostics,
        map_path=args.map_path,
        display=args.display,
        include_imgl=not args.no_imgl,
        include_vql=not args.no_vql,
        write_sidecar=not args.no_sidecar,
        vql_path=args.vql_path,
        svg_path=args.svg_path,
    )

    if args.format == "summary":
        print_json(
            {
                "ok": True,
                "image": ctx.image_path,
                "fingerprint": ctx.fingerprint,
                "nl": ctx.nl,
                "artifacts": ctx.artifacts,
                "imgl": {
                    "ok": ctx.imgl.get("ok"),
                    "windows": ctx.imgl.get("window_count"),
                    "elements": ctx.imgl.get("element_count"),
                },
                "vql": {"path": ctx.artifacts.get("vql"), "svg": ctx.artifacts.get("svg")},
            }
        )
        return 0

    if args.format == "vql":
        program = ctx.vql.get("program") or context_to_vql_program(ctx)
        text = json.dumps(program, indent=2, ensure_ascii=False) + "\n"
        sys.stdout.write(text)
        return 0

    payload = ctx.to_dict()
    payload["reverse"] = reverse_generation_descriptor(ctx)
    print_json({"ok": True, "observe": payload})
    return 0
