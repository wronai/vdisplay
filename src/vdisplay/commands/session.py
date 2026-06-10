"""Shared CLI session flags and CommandRequest helpers."""

from __future__ import annotations

import argparse
from typing import Any

from ..application.commands import CommandRequest, CommandVerb
from .common import control_selector_kwargs_from_args


def add_root_session_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--session",
        action="store_true",
        help="Enable audit session recording under .vdisplay/ (or VDISPLAY_SESSION_DIR)",
    )
    parser.add_argument(
        "--session-id",
        dest="audit_session_id",
        metavar="ID",
        help="Audit session slug (VDISPLAY_SESSION_ID); distinct from control --session-id",
    )


def command_request_from_control_args(args: argparse.Namespace, verb: CommandVerb) -> CommandRequest:
    selector = control_selector_kwargs_from_args(args)
    extra: dict[str, Any] = {
        key: value
        for key, value in selector.items()
        if key
        in {
            "dom_css",
            "dom_xpath",
            "vision_anchor",
            "vision_template",
            "vision_anchor_rel",
            "vision_target",
            "vision_min_confidence",
            "map_path",
            "map_scope",
            "map_target",
        }
        and value is not None
    }
    if getattr(args, "preview", False):
        extra["preview"] = True
    if getattr(args, "preview_output", None):
        extra["preview_output"] = args.preview_output
    if getattr(args, "preview_debug", False):
        extra["preview_debug"] = True

    return CommandRequest(
        verb=verb,
        request_source="cli",
        display=getattr(args, "display", None),
        control_selector=selector.get("selector"),
        control_name=selector.get("name"),
        control_role=selector.get("role"),
        control_app=selector.get("app"),
        control_window_id=selector.get("window_id"),
        control_window_title=selector.get("window_title"),
        control_index=int(selector.get("index") or 0),
        control_environment=selector.get("environment"),
        control_text=selector.get("text"),
        control_text_contains=selector.get("text_contains"),
        control_terminal_line=selector.get("terminal_line"),
        control_terminal_col=selector.get("terminal_col"),
        control_session_id=selector.get("session_id"),
        control_backend=getattr(args, "backend", "auto"),
        control_max_depth=int(getattr(args, "max_depth", 8)),
        control_format=getattr(args, "format", "flat"),
        control_verify=bool(getattr(args, "verify", False)),
        control_screenshot_verify=bool(getattr(args, "screenshot_verify", False)),
        control_verify_label=getattr(args, "verify_label", None),
        control_verify_selector=getattr(args, "verify_selector", None),
        control_value=getattr(args, "value", None),
        extra=extra,
    )
