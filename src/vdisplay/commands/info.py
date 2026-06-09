from __future__ import annotations

import argparse

from ..application.services import info as info_service
from .io import print_json


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("info", help="Show platform capabilities")
    parser.set_defaults(func=handle)


def handle(_args: argparse.Namespace) -> int:
    print_json(info_service.platform_info())
    return 0
