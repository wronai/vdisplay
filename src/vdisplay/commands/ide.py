from __future__ import annotations

import argparse

from ..desktop_apps import list_desktop_apps
from ..exceptions import VDisplayError
from ..ide_prompt import send_ide_prompt
from .common import add_display_arg, add_map_args
from .io import print_json


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("ide", help="IDE prompt helper (launch, focus, type)")
    ide_sub = parser.add_subparsers(dest="action", required=True)

    listing = ide_sub.add_parser("list", help="List IDE apps with control hints")
    listing.set_defaults(func=handle)

    prompt = ide_sub.add_parser("prompt", help="Focus IDE and type a chat prompt")
    add_display_arg(prompt)
    prompt.add_argument("--ide", required=True, help="IDE/app id (pycharm, cursor, vscode, ...)")
    prompt.add_argument("--text", required=True, help="Prompt text to type")
    prompt.add_argument(
        "--backend",
        default=None,
        choices=["auto", "atspi", "x11", "browser", "terminal", "vision"],
        help="Control backend override (default: app profile)",
    )
    prompt.add_argument("--open", action="store_true", help="Launch IDE before typing")
    prompt.add_argument("--variant", help="Launch variant when --open is set")
    prompt.add_argument(
        "--no-wait-window",
        action="store_true",
        help="Skip waiting for app window before focus",
    )
    prompt.add_argument(
        "--wait-timeout",
        type=float,
        default=20.0,
        help="Seconds to wait for app window (default: 20)",
    )
    prompt.add_argument("--submit", action="store_true", help="Click send or submit after typing")
    prompt.add_argument("--verify", action="store_true", help="Verify set-value result")
    add_map_args(prompt)
    prompt.set_defaults(func=handle)


def handle(args: argparse.Namespace) -> int:
    if args.action == "list":
        print_json({"ides": list_desktop_apps(), "count": len(list_desktop_apps())})
        return 0
    if args.action == "prompt":
        try:
            print_json(
                send_ide_prompt(
                    app_id=args.ide,
                    text=args.text,
                    display=getattr(args, "display", None),
                    backend=getattr(args, "backend", None),
                    open_app=bool(getattr(args, "open", False)),
                    launch_variant=getattr(args, "variant", None),
                    wait_window=not bool(getattr(args, "no_wait_window", False)),
                    wait_timeout=float(getattr(args, "wait_timeout", 20.0)),
                    submit=bool(getattr(args, "submit", False)),
                    map_path=getattr(args, "map_path", None),
                    map_scope=getattr(args, "map_scope", None),
                    map_target=getattr(args, "map_target", None),
                    verify=bool(getattr(args, "verify", False)),
                )
            )
        except KeyError as exc:
            raise VDisplayError(str(exc)) from exc
        return 0
    raise VDisplayError(f"unknown ide action: {args.action}")
