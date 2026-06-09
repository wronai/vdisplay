"""Deprecated — use vdisplay.commands and application.services instead."""

from __future__ import annotations

import warnings

from .application.services import capture, discovery, info as info_service
from .commands.io import print_json as _print_json


def print_json(payload: dict) -> None:
    _print_json(payload)


def monitors_payload(*args, **kwargs):
    return discovery.list_monitors(*args, **kwargs)


def windows_payload(*args, **kwargs):
    return discovery.list_windows_payload(*args, **kwargs)


def all_payload(*args, **kwargs):
    return discovery.list_all(*args, **kwargs)


def screenshot_payload(*args, **kwargs):
    warnings.warn("cli_handlers.screenshot_payload is deprecated", DeprecationWarning, stacklevel=2)
    return capture.capture_screenshot(*args, **kwargs)


def dispatch_cli(args):
    warnings.warn("cli_handlers.dispatch_cli is deprecated; use args.func(args)", DeprecationWarning, stacklevel=2)
    return args.func(args)
