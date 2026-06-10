"""HMI live watch — pointer position and keyboard activity."""

from __future__ import annotations

import argparse
import json

from ..hmi.pointer import probe_all_sources
from ..hmi.watch import run_hmi_watch
from .io import print_json


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("hmi", help="Live human-machine interface probes")
    hmi_sub = parser.add_subparsers(dest="action", required=True)

    probe = hmi_sub.add_parser("probe", help="One-shot pointer backend diagnostics")
    probe.add_argument("--display", help="DISPLAY for xdotool (default: auto)")
    probe.add_argument(
        "--no-gtk",
        action="store_true",
        help="Skip GTK pointer probe",
    )
    probe.set_defaults(func=handle)

    watch = hmi_sub.add_parser(
        "watch",
        help="Stream mouse position and keyboard input while you work on another monitor",
    )
    watch.add_argument(
        "--interval",
        type=float,
        default=0.25,
        help="Pointer poll interval in seconds (default: 0.25)",
    )
    watch.add_argument("--display", help="DISPLAY for xdotool (default: auto)")
    watch.add_argument(
        "--no-gtk",
        action="store_true",
        help="Do not probe pointer via GTK (/usr/bin/python3) — xdotool only",
    )
    watch.add_argument(
        "--seed-x",
        type=int,
        default=None,
        help="Manual absolute seed X for evdev tracking",
    )
    watch.add_argument(
        "--seed-y",
        type=int,
        default=None,
        help="Manual absolute seed Y for evdev tracking",
    )
    watch.add_argument(
        "--gtk-every",
        type=int,
        default=None,
        metavar="N",
        help="Query GTK pointer every N polls (default: 1 on Wayland, 4 on X11)",
    )
    watch.add_argument(
        "--no-keyboard",
        action="store_true",
        help="Disable /dev/input keyboard watch (pointer only)",
    )
    watch.add_argument(
        "--no-mouse",
        action="store_true",
        help="Disable /dev/input mouse motion tracking (evdev)",
    )
    watch.add_argument(
        "--jsonl",
        action="store_true",
        help="Emit newline-delimited JSON events",
    )
    watch.set_defaults(func=handle)


def handle(args: argparse.Namespace) -> int:
    if args.action == "probe":
        print_json(probe_all_sources(display=args.display, use_gtk=not args.no_gtk))
        return 0
    if args.action != "watch":
        return 2
    seed_xy = None
    if args.seed_x is not None and args.seed_y is not None:
        seed_xy = (int(args.seed_x), int(args.seed_y))
    elif args.seed_x is not None or args.seed_y is not None:
        raise SystemExit("hmi watch: pass both --seed-x and --seed-y")
    return run_hmi_watch(
        interval=args.interval,
        display=args.display,
        use_gtk=not args.no_gtk,
        gtk_every=args.gtk_every,
        keyboard=not args.no_keyboard,
        mouse=not args.no_mouse,
        seed_xy=seed_xy,
        jsonl=args.jsonl,
    )
