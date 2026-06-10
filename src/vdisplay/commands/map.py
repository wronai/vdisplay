from __future__ import annotations

import argparse

from ..application.services import map as map_svc
from .io import print_json


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("map", help="GUI Map Pack — persistent vision regions/elements (PR-26)")
    map_sub = parser.add_subparsers(dest="action", required=True)

    build = map_sub.add_parser("build", help="Capture screen and build map.json from OCR")
    build.add_argument("--output", required=True, help="Write map.json path")
    build.add_argument("--md", help="Optional operator markdown path")
    build.add_argument("--svg", help="Optional SVG atlas path")
    build.add_argument("--display", default=None, help="X11 display (default: auto)")
    build.add_argument("--monitor", help="Monitor/output name (e.g. DP-2)")
    build.add_argument("--region-id", default="screen", help="Default region id in map")
    build.add_argument("--region-label", help="Human label for default region")
    build.add_argument("--min-confidence", type=float, default=0.5, help="OCR confidence threshold")
    build.set_defaults(func=handle)

    show = map_sub.add_parser("show", help="Show map.json contents")
    show.add_argument("--map", dest="map_path", required=True, help="Path to map.json")
    show.set_defaults(func=handle)

    diff = map_sub.add_parser("diff", help="Detect UI drift vs stored map fingerprints/bounds")
    diff.add_argument("--map", dest="map_path", required=True, help="Path to map.json")
    diff.add_argument("--display", default=None, help="X11 display (default: auto)")
    diff.add_argument("--monitor", help="Monitor/output name override")
    diff.add_argument("--scope", help="Limit diff to one map region id")
    diff.add_argument("--min-confidence", type=float, default=0.5, help="OCR confidence threshold")
    diff.set_defaults(func=handle)

    refresh = map_sub.add_parser("refresh", help="Update map bounds/fingerprints from live capture")
    refresh.add_argument("--map", dest="map_path", required=True, help="Path to map.json")
    refresh.add_argument("--output", help="Write refreshed map (default: overwrite --map)")
    refresh.add_argument("--md", help="Optional refreshed markdown path")
    refresh.add_argument("--svg", help="Optional refreshed SVG path")
    refresh.add_argument("--display", default=None, help="X11 display (default: auto)")
    refresh.add_argument("--monitor", help="Monitor/output name override")
    refresh.add_argument("--scope", help="Limit refresh to one map region id")
    refresh.add_argument("--min-confidence", type=float, default=0.5, help="OCR confidence threshold")
    refresh.add_argument("--add-new", action="store_true", help="Append newly seen OCR labels to the map")
    refresh.set_defaults(func=handle)


def handle(args: argparse.Namespace) -> int:
    if args.action == "build":
        print_json(
            map_svc.map_build(
                display=getattr(args, "display", None),
                output=args.output,
                md=getattr(args, "md", None),
                svg=getattr(args, "svg", None),
                monitor=getattr(args, "monitor", None),
                region_id=getattr(args, "region_id", "screen"),
                region_label=getattr(args, "region_label", None),
                min_confidence=getattr(args, "min_confidence", 0.5),
            )
        )
        return 0
    if args.action == "show":
        print_json(map_svc.map_show(map_path=args.map_path))
        return 0
    if args.action == "diff":
        payload = map_svc.map_diff(
            map_path=args.map_path,
            display=getattr(args, "display", None),
            monitor=getattr(args, "monitor", None),
            scope=getattr(args, "scope", None),
            min_confidence=getattr(args, "min_confidence", 0.5),
        )
        print_json(payload)
        return 0 if payload.get("ok") else 1
    if args.action == "refresh":
        payload = map_svc.map_refresh(
            map_path=args.map_path,
            output=getattr(args, "output", None),
            display=getattr(args, "display", None),
            monitor=getattr(args, "monitor", None),
            scope=getattr(args, "scope", None),
            min_confidence=getattr(args, "min_confidence", 0.5),
            add_new=getattr(args, "add_new", False),
            md=getattr(args, "md", None),
            svg=getattr(args, "svg", None),
        )
        print_json(payload)
        return 0 if payload.get("ok") else 1
    return 1
