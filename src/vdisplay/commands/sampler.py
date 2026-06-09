from __future__ import annotations

import argparse
import json
import sys

from ..application.services.sampler import SamplerConfig, run_sampler
from .common import add_display_arg
from .io import print_json


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser(
        "sampler",
        help="Continuous screenshot loop (watch) — virtual or host ScreenCast",
    )
    subp = parser.add_subparsers(dest="action", required=True)

    start = subp.add_parser("start", help="Start frame sampling loop")
    add_display_arg(start)
    start.add_argument(
        "--mode",
        choices=["desktop", "strict", "unattended", "best-effort"],
        default="desktop",
        help="desktop=host+ScreenCast, strict=virtual :99, unattended=auto",
    )
    start.add_argument("--interval", type=float, default=1.0, help="Seconds between frames")
    start.add_argument("--source", help="Monitor name (e.g. DP-2, primary)")
    start.add_argument("--out-dir", default="./captures", help="Output directory")
    start.add_argument("--max-frames", type=int, default=None, help="Stop after N unique frames")
    start.add_argument("--vd-display", default=":99", help="Virtual display for strict mode")
    start.add_argument("--width", type=int, default=1280)
    start.add_argument("--height", type=int, default=720)
    start.add_argument("--no-dedupe", action="store_true", help="Save duplicate frames")
    start.add_argument("--progress", action="store_true", help="Print one JSON line per frame")
    start.set_defaults(func=handle)


def handle(args: argparse.Namespace) -> int:
    if args.action != "start":
        raise SystemExit(f"unsupported sampler action: {args.action}")

    config = SamplerConfig(
        interval_s=args.interval,
        mode=args.mode,
        source=args.source,
        display=args.display,
        vd_display=args.vd_display,
        output_dir=args.out_dir,
        max_frames=args.max_frames,
        dedupe=not args.no_dedupe,
        width=args.width,
        height=args.height,
    )

    def on_frame(meta: dict) -> None:
        if args.progress:
            line = {
                "frame_index": meta.get("frame_index"),
                "path": meta.get("path") or meta.get("saved"),
                "bytes": meta.get("bytes"),
                "method": meta.get("method"),
            }
            print(json.dumps(line), flush=True)

    result = run_sampler(config, on_frame=on_frame if args.progress else None)
    print_json(result)
    return 0
