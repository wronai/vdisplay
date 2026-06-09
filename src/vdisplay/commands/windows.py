from __future__ import annotations

import argparse

from ..application.services import discovery
from .common import add_display_arg, add_window_filter_args, include_all_from_args
from .io import print_json


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("windows", help="List application windows on the display")
    add_display_arg(parser)
    add_window_filter_args(parser)
    parser.set_defaults(func=handle)


def handle(args: argparse.Namespace) -> int:
    print_json(
        discovery.list_windows_payload(
            args.display,
            include_all=include_all_from_args(args),
            min_width=args.min_width,
            min_height=args.min_height,
            match_class=args.wm_class,
            match_pid=args.pid,
            match_app=args.app,
        )
    )
    return 0
