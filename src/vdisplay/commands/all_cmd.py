from __future__ import annotations

import argparse
import sys
import warnings

from ..application.services import discovery
from .common import add_display_arg, add_window_filter_args, include_all_from_args
from .io import print_json


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("all", help="Show monitors, windows, and adopted state")
    add_display_arg(parser)
    add_window_filter_args(parser)
    parser.set_defaults(func=handle)


def handle(args: argparse.Namespace) -> int:
    print_json(
        discovery.list_all(
            args.display,
            include_all=include_all_from_args(args),
            match_class=args.wm_class,
            match_pid=args.pid,
            match_app=args.app,
        )
    )
    return 0


def register_outputs(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("outputs", help=argparse.SUPPRESS)
    add_display_arg(parser)
    add_window_filter_args(parser)
    parser.set_defaults(func=handle_outputs)


def handle_outputs(args: argparse.Namespace) -> int:
    warnings.warn(
        "vdisplay outputs is deprecated; use vdisplay all (full) or vdisplay monitors",
        DeprecationWarning,
        stacklevel=1,
    )
    print("note: use `vdisplay all` or `vdisplay monitors` instead of `outputs`", file=sys.stderr)
    return handle(args)
