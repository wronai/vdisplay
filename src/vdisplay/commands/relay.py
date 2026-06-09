from __future__ import annotations

import argparse
import sys

from ..application.services import session
from .common import add_display_arg, add_window_filter_args
from .io import print_json
from .windows import handle as handle_windows


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("relay", help="Move windows within the same X11 session")
    relay_sub = parser.add_subparsers(dest="action", required=True)

    radopt = relay_sub.add_parser("adopt-window", help="Move window off-screen or to target output")
    radopt.add_argument("--title")
    radopt.add_argument("--window-id")
    radopt.add_argument("--class", dest="wm_class", help="Match WM_CLASS / instance")
    radopt.add_argument("--pid", type=int, help="Match process ID")
    radopt.add_argument("--app", help="Match app_label / process_name")
    radopt.add_argument("--target", default="offscreen")
    radopt.add_argument("--display", default=None)
    radopt.set_defaults(func=handle)

    rrelease = relay_sub.add_parser("release-window", help="Restore adopted window")
    rrelease.add_argument("--title")
    rrelease.add_argument("--window-id")
    rrelease.add_argument("--class", dest="wm_class")
    rrelease.add_argument("--pid", type=int)
    rrelease.add_argument("--app")
    rrelease.add_argument("--display", default=None)
    rrelease.set_defaults(func=handle)

    rlist = relay_sub.add_parser("list", help="List adopted (off-screen) windows")
    rlist.add_argument("--display", default=None)
    rlist.set_defaults(func=handle)

    rshot = relay_sub.add_parser("screenshot", help="Capture host monitor screenshot")
    rshot.add_argument("-o", "--output", required=True)
    rshot.add_argument("--monitor", type=int, default=1, help="Monitor index (1-based)")
    rshot.add_argument("--source", default=None, help="Monitor name (overrides --monitor)")
    rshot.add_argument("--display", default=None)
    rshot.set_defaults(func=handle)

    rwindows = relay_sub.add_parser("list-windows", help="Deprecated: use vdisplay windows")
    add_display_arg(rwindows)
    add_window_filter_args(rwindows)
    rwindows.set_defaults(func=handle_list_windows)


def handle_list_windows(args: argparse.Namespace) -> int:
    print("note: use `vdisplay windows` instead of `relay list-windows`", file=sys.stderr)
    return handle_windows(args)


def handle(args: argparse.Namespace) -> int:
    if args.action == "adopt-window":
        print_json(
            session.relay_adopt(
                display=args.display,
                match_title=args.title,
                window_id=args.window_id,
                match_class=args.wm_class,
                match_pid=args.pid,
                match_app=args.app,
                target=args.target,
            )
        )
        return 0
    if args.action == "release-window":
        print_json(
            session.relay_release(
                display=args.display,
                match_title=args.title,
                window_id=args.window_id,
                match_class=args.wm_class,
                match_pid=args.pid,
                match_app=args.app,
            )
        )
        return 0
    if args.action == "list":
        print_json(session.relay_list_adopted(args.display))
        return 0
    if args.action == "screenshot":
        print_json(
            session.relay_screenshot(
                args.output,
                monitor=args.monitor,
                display=args.display,
                source=args.source,
            )
        )
        return 0
    session.unsupported_session_action("relay", args.action)
    return 1
