from __future__ import annotations

import argparse

from ..application.services import discovery
from .common import add_all_arg, add_display_arg, include_all_from_args
from .io import print_json


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("monitors", help="List connected monitors (xrandr)")
    add_display_arg(parser)
    add_all_arg(parser)
    parser.set_defaults(func=handle)


def handle(args: argparse.Namespace) -> int:
    print_json(discovery.list_monitors(args.display, include_all=include_all_from_args(args)))
    return 0
