from __future__ import annotations

import argparse

from ..application.commands import CommandVerb
from ..application.executor import execute
from ..application.services import session as session_svc
from ..exceptions import VDisplayError
from .common import (
    add_control_selector_args,
    add_display_arg,
    add_map_args,
    add_preview_args,
    control_selector_kwargs_for_service,
)
from .io import print_json
from .session import command_request_from_control_args


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


def _run_control(args: argparse.Namespace, verb: CommandVerb) -> int:
    result = execute(command_request_from_control_args(args, verb))
    print_json(result.data if result.ok else result.to_dict())
    if not result.ok:
        message = result.error.message if result.error else "control command failed"
        raise VDisplayError(message)
    return 0 if result.data.get("ok", True) else 1


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
    from ..application.commands import CommandRequest

    result = execute(
        CommandRequest(
            verb=CommandVerb.CONTROLS_LIST,
            request_source="cli",
            display=args.display,
            control_window_id=args.window_id,
            control_app=args.app,
            control_backend=args.backend,
            control_max_depth=args.max_depth,
            control_format=args.format,
            control_session_id=getattr(args, "session_id", None),
        )
    )
    print_json(result.data if result.ok else result.to_dict())
    if not result.ok:
        message = result.error.message if result.error else "control list failed"
        raise VDisplayError(message)
    return 0


def _handle_control_find(args: argparse.Namespace) -> int:
    return _run_control(args, CommandVerb.CONTROLS_FIND)


def _handle_control_click(args: argparse.Namespace) -> int:
    return _run_control(args, CommandVerb.CONTROL_CLICK)


def _handle_control_focus(args: argparse.Namespace) -> int:
    return _run_control(args, CommandVerb.CONTROL_FOCUS)


def _handle_control_set_value(args: argparse.Namespace) -> int:
    return _run_control(args, CommandVerb.CONTROL_SET_VALUE)


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
