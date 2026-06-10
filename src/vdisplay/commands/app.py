from __future__ import annotations

import argparse

from ..desktop_apps import get_desktop_app, list_desktop_apps
from ..exceptions import VDisplayError
from ..ide_prompt import open_desktop_app
from .io import print_json


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("app", help="Desktop application launcher registry")
    app_sub = parser.add_subparsers(dest="action", required=True)

    listing = app_sub.add_parser("list", help="List known desktop/IDE apps")
    listing.set_defaults(func=handle)

    show = app_sub.add_parser("show", help="Show one app profile")
    show.add_argument("app_id", help="App id (e.g. pycharm, cursor)")
    show.set_defaults(func=handle)

    open_cmd = app_sub.add_parser("open", help="Launch a desktop/IDE app")
    open_cmd.add_argument("app_id", help="App id (e.g. pycharm, cursor)")
    open_cmd.add_argument(
        "--variant",
        help="Launch variant (default, desktop, default-xwayland, ...)",
    )
    open_cmd.add_argument(
        "--wait",
        type=float,
        default=1.0,
        help="Seconds to sleep after launch (default: 1.0)",
    )
    open_cmd.set_defaults(func=handle)


def handle(args: argparse.Namespace) -> int:
    if args.action == "list":
        print_json({"apps": list_desktop_apps(), "count": len(list_desktop_apps())})
        return 0
    if args.action == "show":
        try:
            print_json(get_desktop_app(args.app_id).to_dict())
        except KeyError as exc:
            raise VDisplayError(str(exc)) from exc
        return 0
    if args.action == "open":
        try:
            print_json(
                open_desktop_app(
                    args.app_id,
                    variant=getattr(args, "variant", None),
                    wait_seconds=float(getattr(args, "wait", 1.0)),
                )
            )
        except KeyError as exc:
            raise VDisplayError(str(exc)) from exc
        return 0
    raise VDisplayError(f"unknown app action: {args.action}")
