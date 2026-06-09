from __future__ import annotations

import argparse

from ..application.services import control as control_svc
from .common import add_display_arg
from .io import print_json


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("control", help="Accessibility-first UI control (AT-SPI / x11 fallback)")
    control_sub = parser.add_subparsers(dest="action", required=True)

    listing = control_sub.add_parser("list", help="List controls from accessibility tree")
    add_display_arg(listing)
    listing.add_argument("--app", help="Filter by application name")
    listing.add_argument("--window-id", help="Filter by X11 window id")
    listing.add_argument("--backend", default="auto", choices=["auto", "atspi", "x11"])
    listing.add_argument("--format", default="flat", choices=["flat", "tree"])
    listing.add_argument("--max-depth", type=int, default=8)
    listing.set_defaults(func=handle)

    finding = control_sub.add_parser("find", help="Find controls by selector")
    add_display_arg(finding)
    _add_selector_args(finding)
    finding.set_defaults(func=handle)

    click = control_sub.add_parser("click", help="Invoke control (button/menu)")
    add_display_arg(click)
    _add_selector_args(click)
    click.add_argument("--verify", action="store_true")
    click.set_defaults(func=handle)

    focus = control_sub.add_parser("focus", help="Focus control")
    add_display_arg(focus)
    _add_selector_args(focus)
    focus.set_defaults(func=handle)

    set_value = control_sub.add_parser("set-value", help="Set text/value on input")
    add_display_arg(set_value)
    _add_selector_args(set_value)
    set_value.add_argument("--value", required=True)
    set_value.add_argument("--verify", action="store_true")
    set_value.set_defaults(func=handle)


def _add_selector_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--selector", help='e.g. button[name="Save"]')
    parser.add_argument("--name", help="Exact control name")
    parser.add_argument("--role", help="Control role (button, input, ...)")
    parser.add_argument("--app", help="Application label")
    parser.add_argument("--window-id")
    parser.add_argument("--index", type=int, default=0)
    parser.add_argument("--backend", default="auto", choices=["auto", "atspi", "x11"])


def _selector_kwargs(args: argparse.Namespace) -> dict:
    return {
        "selector": args.selector,
        "name": args.name,
        "role": args.role,
        "app": args.app,
        "window_id": args.window_id,
        "index": args.index,
    }


def handle(args: argparse.Namespace) -> int:
    if args.action == "list":
        print_json(
            control_svc.controls_list(
                display=args.display,
                window_id=args.window_id,
                app=args.app,
                backend=args.backend,
                max_depth=args.max_depth,
                format=args.format,
            )
        )
        return 0
    if args.action == "find":
        print_json(
            control_svc.controls_find(
                display=args.display,
                backend=args.backend,
                **_selector_kwargs(args),
            )
        )
        return 0
    if args.action == "click":
        print_json(
            control_svc.control_click(
                display=args.display,
                backend=args.backend,
                verify=args.verify,
                **_selector_kwargs(args),
            )
        )
        return 0
    if args.action == "focus":
        print_json(
            control_svc.control_focus(
                display=args.display,
                backend=args.backend,
                **_selector_kwargs(args),
            )
        )
        return 0
    if args.action == "set-value":
        print_json(
            control_svc.control_set_value(
                display=args.display,
                backend=args.backend,
                verify=args.verify,
                value=args.value,
                **_selector_kwargs(args),
            )
        )
        return 0
    return 1
