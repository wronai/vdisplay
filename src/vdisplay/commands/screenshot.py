from __future__ import annotations

import argparse

from ..application.config_options import get_runtime_options
from ..application.services import capture
from .common import add_display_arg
from .io import print_json


def register(sub: argparse._SubParsersAction) -> None:
    opts = get_runtime_options()
    parser = sub.add_parser("screenshot", help="Capture monitor screenshot (mirror on multi-monitor host)")
    add_display_arg(parser)
    parser.add_argument("-o", "--output", help="Output PNG path")
    parser.add_argument("--out-dir", help="Output directory for --all-monitors")
    parser.add_argument("--monitor", type=int, help="Monitor index (1-based)")
    parser.add_argument("--source", help="Monitor name (e.g. DP-2, HDMI-1)")
    parser.add_argument("--target", help="Mirror target output (optional)")
    parser.add_argument("--all-monitors", action="store_true", help="Capture every connected monitor")
    parser.add_argument(
        "--mode",
        choices=opts.screenshot_sources,
        default="host",
        help="Capture backend (default: host/mirror pipeline)",
    )
    parser.add_argument("--width", type=int, default=1280, help="Virtual mode width")
    parser.add_argument("--height", type=int, default=720, help="Virtual mode height")
    parser.add_argument("--vd-display", default=":99", help="Virtual mode DISPLAY")
    parser.add_argument(
        "--no-img2nl",
        action="store_true",
        help="Skip img2nl scene description in JSON output",
    )
    parser.set_defaults(func=handle)


def handle(args: argparse.Namespace) -> int:
    print_json(
        capture.capture_screenshot(
            output=args.output,
            display=args.display,
            monitor=args.monitor,
            source=args.source,
            target=args.target,
            mode=args.mode,
            all_monitors=args.all_monitors,
            out_dir=args.out_dir,
            width=args.width,
            height=args.height,
            vd_display=args.vd_display,
            skip_img2nl=args.no_img2nl,
        )
    )
    return 0
