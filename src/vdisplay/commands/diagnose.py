from __future__ import annotations

import argparse

from ..application.services import discovery
from .common import add_display_arg
from .io import print_json


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("diagnose", help="Diagnose DISPLAY and monitor visibility")
    add_display_arg(parser)
    parser.add_argument(
        "--unattended",
        action="store_true",
        help="Assess prompt-free continuous capture (sampler / watch)",
    )
    parser.add_argument(
        "--control",
        action="store_true",
        help="Assess accessibility-first control backends (AT-SPI / x11 fallback)",
    )
    parser.set_defaults(func=handle)


def handle(args: argparse.Namespace) -> int:
    if args.control:
        from ..application.services import control as control_svc

        print_json(control_svc.diagnose_control(display=args.display))
        return 0
    if args.unattended:
        print_json(discovery.diagnose_unattended(args.display))
        return 0
    print_json(discovery.diagnose(args.display))
    return 0
