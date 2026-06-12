from __future__ import annotations

import argparse

from ..application.services import discovery
from .common import add_display_arg, add_window_filter_args, include_all_from_args
from .io import print_json


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("windows", help="List application windows on the display")
    add_display_arg(parser)
    add_window_filter_args(parser)
    parser.set_defaults(func=handle)


def handle(args: argparse.Namespace) -> int:
    payload = discovery.list_windows_payload(
        args.display,
        include_all=include_all_from_args(args),
        min_width=args.min_width,
        min_height=args.min_height,
        match_class=args.wm_class,
        match_pid=args.pid,
        match_app=args.app,
        correlate=bool(getattr(args, "correlate", False)),
    )
    if bool(getattr(args, "app_surfaces", False)):
        if not payload.get("correlated"):
            payload = discovery.list_windows_payload(
                args.display,
                include_all=include_all_from_args(args),
                min_width=args.min_width,
                min_height=args.min_height,
                match_class=args.wm_class,
                match_pid=args.pid,
                match_app=args.app,
                correlate=True,
            )
        print_json(
            {
                "app_surface_count": payload.get("app_surface_count", 0),
                "jetbrains_awt_proxy_count": payload.get("jetbrains_awt_proxy_count", 0),
                "app_surfaces": payload.get("app_surfaces") or [],
                "correlation_sources": payload.get("correlation_sources") or {},
            }
        )
        return 0
    print_json(payload)
    return 0
