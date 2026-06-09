from __future__ import annotations

import argparse

from ..application.services import session
from .io import print_json


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("mirror", help="Mirror an existing display")
    mirror_sub = parser.add_subparsers(dest="action", required=True)

    mstart = mirror_sub.add_parser("start", help="Start mirror session")
    mstart.add_argument("--backend", default="x11")
    mstart.add_argument("--source", default="primary")
    mstart.add_argument("--target", default=None)
    mstart.add_argument("--display", default=None)
    mstart.add_argument("-o", "--output", default=None, help="Optional screenshot path")
    mstart.set_defaults(func=handle)

    mshot = mirror_sub.add_parser("screenshot", help="Capture mirrored monitor screenshot")
    mshot.add_argument("-o", "--output", required=True)
    mshot.add_argument("--source", default="primary", help="Source monitor name or primary")
    mshot.add_argument("--target", default=None, help="Mirror target output")
    mshot.add_argument("--display", default=None)
    mshot.add_argument("--backend", default="x11")
    mshot.set_defaults(func=handle)


def handle(args: argparse.Namespace) -> int:
    if args.action == "start":
        print_json(
            session.mirror_start(
                source=args.source,
                target=args.target,
                backend=args.backend,
                display=args.display,
                output=args.output,
            )
        )
        return 0
    if args.action == "screenshot":
        print_json(
            session.mirror_screenshot(
                args.output,
                source=args.source,
                target=args.target,
                display=args.display,
            )
        )
        return 0
    session.unsupported_session_action("mirror", args.action)
    return 1
