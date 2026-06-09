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
    listing.add_argument("--backend", default="auto", choices=["auto", "atspi", "x11", "browser", "terminal"])
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
    click.add_argument("--screenshot-verify", action="store_true", help="Verify action via before/after screenshot diff")
    click.add_argument("--verify-label", help="Expect label text_value with this prefix to change")
    click.add_argument("--verify-selector", help='Verify change on another control, e.g. label[name="counter-label"]')
    click.set_defaults(func=handle)

    focus = control_sub.add_parser("focus", help="Focus control")
    add_display_arg(focus)
    _add_selector_args(focus)
    focus.add_argument("--verify", action="store_true")
    focus.add_argument("--screenshot-verify", action="store_true", help="Verify action via before/after screenshot diff")
    focus.set_defaults(func=handle)

    set_value = control_sub.add_parser("set-value", help="Set text/value on input")
    add_display_arg(set_value)
    _add_selector_args(set_value)
    set_value.add_argument("--value", required=True)
    set_value.add_argument("--verify", action="store_true")
    set_value.add_argument("--screenshot-verify", action="store_true", help="Verify action via before/after screenshot diff")
    set_value.add_argument("--verify-label", help="Expect label text_value with this prefix to change")
    set_value.add_argument("--verify-selector", help="Verify change on another control after set-value")
    set_value.set_defaults(func=handle)


def _add_selector_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--selector", help='e.g. button[name="Save"] or line[3][text="OK"]')
    parser.add_argument("--name", help="Exact control name")
    parser.add_argument("--role", help="Control role (button, input, ...)")
    parser.add_argument("--app", help="Application label or window title")
    parser.add_argument("--window-title", help="Window/frame title filter")
    parser.add_argument("--window-id")
    parser.add_argument("--index", type=int, default=0)
    parser.add_argument("--backend", default="auto", choices=["auto", "atspi", "x11", "browser", "terminal"])
    parser.add_argument("--environment", choices=["desktop", "browser", "terminal", "vision"])
    parser.add_argument("--text", help="Exact visible text match")
    parser.add_argument("--text-contains", help="Substring text match")
    parser.add_argument("--terminal-line", type=int, help="1-based terminal line number")
    parser.add_argument("--terminal-col", type=int, help="1-based terminal column number")
    parser.add_argument("--session-id", help="Terminal or browser session id")


def _selector_kwargs(args: argparse.Namespace) -> dict:
    return {
        "selector": args.selector,
        "name": args.name,
        "role": args.role,
        "app": args.app,
        "window_title": getattr(args, "window_title", None),
        "window_id": args.window_id,
        "index": args.index,
        "environment": getattr(args, "environment", None),
        "text": getattr(args, "text", None),
        "text_contains": getattr(args, "text_contains", None),
        "terminal_line": getattr(args, "terminal_line", None),
        "terminal_col": getattr(args, "terminal_col", None),
        "session_id": getattr(args, "session_id", None),
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
                screenshot_verify=getattr(args, "screenshot_verify", False),
                verify_label=getattr(args, "verify_label", None),
                verify_selector=getattr(args, "verify_selector", None),
                **_selector_kwargs(args),
            )
        )
        return 0
    if args.action == "focus":
        print_json(
            control_svc.control_focus(
                display=args.display,
                backend=args.backend,
                verify=args.verify,
                screenshot_verify=getattr(args, "screenshot_verify", False),
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
                screenshot_verify=getattr(args, "screenshot_verify", False),
                verify_label=getattr(args, "verify_label", None),
                verify_selector=getattr(args, "verify_selector", None),
                value=args.value,
                **_selector_kwargs(args),
            )
        )
        return 0
    return 1
