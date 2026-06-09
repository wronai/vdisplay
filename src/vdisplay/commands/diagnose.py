from __future__ import annotations

import argparse

from ..application.services import discovery
from .common import add_display_arg
from .io import print_json


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("diagnose", help="Diagnose DISPLAY and monitor visibility")
    add_display_arg(parser)
    parser.set_defaults(func=handle)


def handle(args: argparse.Namespace) -> int:
    print_json(discovery.diagnose(args.display))
    return 0
