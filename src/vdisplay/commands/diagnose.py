from __future__ import annotations

import argparse

from ..application.services import discovery
from .common import add_control_selector_args, add_display_arg, add_preview_args, control_selector_kwargs_for_service
from .io import print_json


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("diagnose", help="Diagnose DISPLAY and monitor visibility")
    add_display_arg(parser)
    parser.add_argument(
        "aspect",
        nargs="?",
        choices=["control", "unattended"],
        help="Aspect to diagnose",
    )
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
    add_control_selector_args(parser)
    add_preview_args(parser)
    parser.set_defaults(func=handle)


def handle(args: argparse.Namespace) -> int:
    if args.control or getattr(args, "aspect", None) == "control":
        from ..application.services import control as control_svc

        print_json(
            control_svc.diagnose_control(
                display=args.display,
                backend=getattr(args, "backend", "auto"),
                preview=getattr(args, "preview", False),
                preview_output=getattr(args, "preview_output", None),
                preview_debug=getattr(args, "preview_debug", False),
                **control_selector_kwargs_for_service(args),
            )
        )
        return 0
    if args.unattended or getattr(args, "aspect", None) == "unattended":
        print_json(discovery.diagnose_unattended(args.display))
        return 0
    print_json(discovery.diagnose(args.display))
    return 0
