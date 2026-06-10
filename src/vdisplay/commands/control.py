from __future__ import annotations

import argparse

from ..application.services import control as control_svc
from ..application.services import session as session_svc
from .common import (
    add_control_selector_args,
    add_display_arg,
    add_map_args,
    add_preview_args,
    control_selector_kwargs_for_service,
)
from .io import print_json


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("control", help="Accessibility-first UI control (AT-SPI / x11 fallback)")
    control_sub = parser.add_subparsers(dest="action", required=True)

    listing = control_sub.add_parser("list", help="List controls from accessibility tree")
    add_display_arg(listing)
    listing.add_argument("--app", help="Filter by application name")
    listing.add_argument("--window-id", help="Filter by X11 window id")
    listing.add_argument(
        "--backend",
        default="auto",
        choices=["auto", "atspi", "x11", "browser", "terminal", "vision"],
    )
    listing.add_argument("--session-id", help="Terminal or browser session id")
    listing.add_argument("--format", default="flat", choices=["flat", "tree"])
    listing.add_argument("--max-depth", type=int, default=8)
    listing.set_defaults(func=handle)

    finding = control_sub.add_parser("find", help="Find controls by selector")
    add_display_arg(finding)
    _add_selector_args(finding)
    add_preview_args(finding)
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

    browser_open = control_sub.add_parser("browser-open", help="Open Playwright browser session")
    browser_open.add_argument("--url", required=True, help="Initial page URL")
    browser_open.add_argument("--session-id", required=True, help="Session id for later control commands")
    browser_open.add_argument("--headed", action="store_true", help="Show browser window (default: headless)")
    browser_open.add_argument("--vendor", choices=["chromium", "firefox"], help="Browser engine vendor")
    browser_open.add_argument("--engine", help="Alias for --vendor (chromium, firefox, chrome)")
    browser_open.set_defaults(func=handle)


def _add_selector_args(parser: argparse.ArgumentParser) -> None:
    add_control_selector_args(parser)
    add_map_args(parser)


def _handle_browser_open(args: argparse.Namespace) -> int:
    engine = getattr(args, "vendor", None) or getattr(args, "engine", None)
    print_json(
        session_svc.browser_open(
            url=args.url,
            session_id=args.session_id,
            headless=not getattr(args, "headed", False),
            engine=engine,
        )
    )
    return 0


def _handle_control_list(args: argparse.Namespace) -> int:
    print_json(
        control_svc.controls_list(
            display=args.display,
            window_id=args.window_id,
            app=args.app,
            backend=args.backend,
            max_depth=args.max_depth,
            format=args.format,
            session_id=getattr(args, "session_id", None),
        )
    )
    return 0


def _handle_control_find(args: argparse.Namespace) -> int:
    print_json(
        control_svc.controls_find(
            display=args.display,
            backend=args.backend,
            preview=getattr(args, "preview", False),
            preview_output=getattr(args, "preview_output", None),
            preview_debug=getattr(args, "preview_debug", False),
            **control_selector_kwargs_for_service(args),
        )
    )
    return 0


def _handle_control_click(args: argparse.Namespace) -> int:
    print_json(
        control_svc.control_click(
            display=args.display,
            backend=args.backend,
            verify=args.verify,
            screenshot_verify=getattr(args, "screenshot_verify", False),
            verify_label=getattr(args, "verify_label", None),
            verify_selector=getattr(args, "verify_selector", None),
            **control_selector_kwargs_for_service(args),
        )
    )
    return 0


def _handle_control_focus(args: argparse.Namespace) -> int:
    print_json(
        control_svc.control_focus(
            display=args.display,
            backend=args.backend,
            verify=args.verify,
            screenshot_verify=getattr(args, "screenshot_verify", False),
            **control_selector_kwargs_for_service(args),
        )
    )
    return 0


def _handle_control_set_value(args: argparse.Namespace) -> int:
    print_json(
        control_svc.control_set_value(
            display=args.display,
            backend=args.backend,
            verify=args.verify,
            screenshot_verify=getattr(args, "screenshot_verify", False),
            verify_label=getattr(args, "verify_label", None),
            verify_selector=getattr(args, "verify_selector", None),
            value=args.value,
            **control_selector_kwargs_for_service(args),
        )
    )
    return 0


_CONTROL_HANDLERS = {
    "browser-open": _handle_browser_open,
    "list": _handle_control_list,
    "find": _handle_control_find,
    "click": _handle_control_click,
    "focus": _handle_control_focus,
    "set-value": _handle_control_set_value,
}


def handle(args: argparse.Namespace) -> int:
    handler = _CONTROL_HANDLERS.get(args.action)
    if handler is None:
        return 1
    return handler(args)
