from __future__ import annotations

import argparse

from ..application.services import session
from ..exceptions import VDisplayError
from .io import print_json


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("virtual", help="Private virtual display session")
    virtual_sub = parser.add_subparsers(dest="action", required=True)

    vstart = virtual_sub.add_parser("start", help="Start Xvfb virtual display")
    vstart.add_argument("--backend", default="xvfb")
    vstart.add_argument("--width", type=int, default=1920)
    vstart.add_argument("--height", type=int, default=1080)
    vstart.add_argument("--display", default=":99")
    vstart.set_defaults(func=handle)

    vlaunch = virtual_sub.add_parser("launch", help="Launch command on active virtual display")
    vlaunch.add_argument("--backend", default="xvfb")
    vlaunch.add_argument("--width", type=int, default=1920)
    vlaunch.add_argument("--height", type=int, default=1080)
    vlaunch.add_argument("--display", default=":99")
    vlaunch.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command and args (e.g. xterm -hold). Optional leading -- is stripped.",
    )
    vlaunch.set_defaults(func=handle)

    vshot = virtual_sub.add_parser("screenshot", help="Capture virtual display screenshot")
    vshot.add_argument("-o", "--output", required=True)
    vshot.add_argument("--backend", default="xvfb")
    vshot.add_argument("--width", type=int, default=1920)
    vshot.add_argument("--height", type=int, default=1080)
    vshot.add_argument("--display", default=":99")
    vshot.set_defaults(func=handle)


def handle(args: argparse.Namespace) -> int:
    if args.action == "start":
        print_json(
            session.virtual_start(
                width=args.width,
                height=args.height,
                backend=args.backend,
                display=args.display,
            )
        )
        return 0
    if args.action == "launch":
        command = list(args.command)
        if command[:1] == ["--"]:
            command = command[1:]
        if not command:
            raise VDisplayError("virtual launch requires a command (e.g. xterm -hold)")
        print_json(
            session.virtual_launch(
                command,
                width=args.width,
                height=args.height,
                backend=args.backend,
                display=args.display,
            )
        )
        return 0
    if args.action == "screenshot":
        print_json(
            session.virtual_screenshot(
                args.output,
                width=args.width,
                height=args.height,
                backend=args.backend,
                display=args.display,
            )
        )
        return 0
    session.unsupported_session_action("virtual", args.action)
    return 1
