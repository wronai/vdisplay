from __future__ import annotations

import argparse


def add_display_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--display", default=None, help="X11 display (default: auto-resolve host :0)")


def add_all_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--all",
        dest="include_all",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include all entries (default: true)",
    )


def add_window_filter_args(parser: argparse.ArgumentParser) -> None:
    add_all_arg(parser)
    parser.add_argument(
        "--apps-only",
        action="store_true",
        help="Application windows only (same as --no-all)",
    )
    parser.add_argument("--min-width", type=int, default=0)
    parser.add_argument("--min-height", type=int, default=0)
    parser.add_argument("--class", dest="wm_class", help="Filter by WM_CLASS")
    parser.add_argument("--pid", type=int, help="Filter by process ID")
    parser.add_argument("--app", help="Filter by app_label / process_name")


def include_all_from_args(args: argparse.Namespace) -> bool:
    return bool(getattr(args, "include_all", True) and not getattr(args, "apps_only", False))


_CONTROL_BACKEND_CHOICES = ["auto", "atspi", "x11", "browser", "terminal", "vision"]


def add_control_selector_args(parser: argparse.ArgumentParser) -> None:
    """Selector/session flags shared by control and diagnose control."""
    parser.add_argument("--selector", help='e.g. #submit, button[name="Save"], line[3]')
    parser.add_argument("--name", help="Exact control name")
    parser.add_argument("--role", help="Control role (button, input, ...)")
    parser.add_argument("--app", help="Application label or window title")
    parser.add_argument("--window-title", help="Window/frame title filter")
    parser.add_argument("--window-id")
    parser.add_argument("--index", type=int, default=0)
    parser.add_argument(
        "--backend",
        default="auto",
        choices=_CONTROL_BACKEND_CHOICES,
    )
    parser.add_argument("--environment", choices=["desktop", "browser", "terminal", "vision"])
    parser.add_argument("--text", help="Exact visible text match")
    parser.add_argument("--text-contains", help="Substring text match")
    parser.add_argument("--terminal-line", type=int, help="1-based terminal line number")
    parser.add_argument("--terminal-col", type=int, help="1-based terminal column number")
    parser.add_argument("--session-id", help="Terminal or browser session id")
    parser.add_argument("--dom-css", help="CSS selector for browser/DOM control")
    parser.add_argument("--dom-xpath", help="XPath selector for browser/DOM control")
    parser.add_argument("--vision-anchor", help="Vision OCR anchor text")
    parser.add_argument("--vision-template", help="Vision template PNG path or base64")
    parser.add_argument(
        "--vision-anchor-rel",
        choices=["right_of", "below", "near", "left_of", "above"],
        help="Spatial relation from vision anchor to target",
    )
    parser.add_argument("--vision-target", help="Vision target text relative to anchor")


def control_selector_kwargs_from_args(args: argparse.Namespace) -> dict:
    return {
        "selector": getattr(args, "selector", None),
        "name": getattr(args, "name", None),
        "role": getattr(args, "role", None),
        "app": getattr(args, "app", None),
        "window_title": getattr(args, "window_title", None),
        "window_id": getattr(args, "window_id", None),
        "index": getattr(args, "index", 0),
        "backend": getattr(args, "backend", "auto"),
        "environment": getattr(args, "environment", None),
        "text": getattr(args, "text", None),
        "text_contains": getattr(args, "text_contains", None),
        "terminal_line": getattr(args, "terminal_line", None),
        "terminal_col": getattr(args, "terminal_col", None),
        "session_id": getattr(args, "session_id", None),
        "dom_css": getattr(args, "dom_css", None),
        "dom_xpath": getattr(args, "dom_xpath", None),
        "vision_anchor": getattr(args, "vision_anchor", None),
        "vision_template": getattr(args, "vision_template", None),
        "vision_anchor_rel": getattr(args, "vision_anchor_rel", None),
        "vision_target": getattr(args, "vision_target", None),
    }


def control_selector_kwargs_for_service(args: argparse.Namespace) -> dict:
    """Selector kwargs without ``backend`` — pass ``backend=args.backend`` explicitly."""
    payload = control_selector_kwargs_from_args(args)
    payload.pop("backend", None)
    return payload
