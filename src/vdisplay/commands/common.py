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
