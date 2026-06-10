"""Shared helpers for control-plane command handlers."""

from __future__ import annotations

from typing import Any

from ..commands import CommandRequest


def control_selector_kwargs(cmd: CommandRequest) -> dict[str, Any]:
    return {
        "selector": cmd.control_selector,
        "provider_ref": cmd.control_provider_ref,
        "name": cmd.control_name,
        "role": cmd.control_role,
        "app": cmd.control_app,
        "window_id": cmd.control_window_id,
        "window_title": cmd.control_window_title,
        "index": cmd.control_index,
        "environment": cmd.control_environment,
        "text": cmd.control_text,
        "text_contains": cmd.control_text_contains,
        "terminal_line": cmd.control_terminal_line,
        "terminal_col": cmd.control_terminal_col,
        "session_id": cmd.control_session_id,
    }


def control_service_kwargs(cmd: CommandRequest) -> dict[str, Any]:
    payload = control_selector_kwargs(cmd)
    payload.update({key: value for key, value in cmd.extra.items() if value is not None})
    return payload


def control_selector_only_kwargs(cmd: CommandRequest) -> dict[str, Any]:
    """Selector kwargs for service calls — strips fields passed explicitly by handlers."""
    reserved = {
        "backend",
        "display",
        "verify",
        "screenshot_verify",
        "verify_label",
        "verify_selector",
        "value",
        "preview",
        "preview_output",
        "preview_debug",
        "max_depth",
        "format",
    }
    kwargs = control_service_kwargs(cmd)
    for key in reserved:
        kwargs.pop(key, None)
    return kwargs


def control_request_body(cmd: CommandRequest) -> dict[str, Any]:
    body = control_service_kwargs(cmd)
    body.update(
        {
            "display": cmd.display,
            "backend": cmd.control_backend,
            "verify": cmd.control_verify,
            "screenshot_verify": cmd.control_screenshot_verify,
            "verify_label": cmd.control_verify_label,
            "verify_selector": cmd.control_verify_selector,
            "value": cmd.control_value,
            "max_depth": cmd.control_max_depth,
            "format": cmd.control_format,
        }
    )
    return {key: value for key, value in body.items() if value is not None}
