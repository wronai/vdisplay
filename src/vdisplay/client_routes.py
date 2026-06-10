"""Map CommandRequest verbs to vdisplay-agent broker HTTP routes."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .application.commands import CommandRequest, CommandVerb
from .exceptions import VDisplayError


def _route_outputs_query(cmd: CommandRequest) -> tuple[str, str, dict[str, Any] | None]:
    """Route MONITORS/OUTPUTS commands."""
    query: list[str] = []
    if cmd.display:
        query.append(f"display={cmd.display}")
    if not cmd.include_all:
        query.append("include_all=false")
    suffix = f"?{'&'.join(query)}" if query else ""
    return "GET", f"/outputs{suffix}", None


def _route_windows_query(cmd: CommandRequest) -> tuple[str, str, dict[str, Any] | None]:
    """Route WINDOWS command with query parameters."""
    params = {
        "display": cmd.display,
        "include_all": str(cmd.include_all).lower(),
        "match_class": cmd.match_class,
        "match_pid": cmd.match_pid,
        "match_app": cmd.match_app,
        "min_width": cmd.min_width or None,
        "min_height": cmd.min_height or None,
    }
    query = [f"{key}={value}" for key, value in params.items() if value is not None]
    suffix = f"?{'&'.join(query)}" if query else ""
    return "GET", f"/windows{suffix}", None


def _route_control_command(verb: CommandVerb, body: dict[str, Any]) -> tuple[str, str, dict[str, Any] | None]:
    """Route control-related commands."""
    if verb == CommandVerb.CONTROLS_LIST:
        return "POST", "/controls/list", body
    if verb == CommandVerb.CONTROLS_FIND:
        return "POST", "/controls/find", body
    if verb == CommandVerb.CONTROL_CLICK:
        return "POST", "/control/invoke", body
    if verb == CommandVerb.CONTROL_FOCUS:
        return "POST", "/control/focus", body
    return "POST", "/control/set-value", body


def _route_terminal_open(cmd: CommandRequest) -> tuple[str, str, dict[str, Any] | None]:
    body: dict[str, Any] = {
        "rows": cmd.terminal_rows,
        "cols": cmd.terminal_cols,
    }
    if cmd.terminal_session_id:
        body["session_id"] = cmd.terminal_session_id
    if cmd.terminal_command:
        body["command"] = cmd.terminal_command
    if cmd.terminal_title:
        body["title"] = cmd.terminal_title
    return "POST", "/session/terminal/open", body


def _route_browser_open(cmd: CommandRequest) -> tuple[str, str, dict[str, Any] | None]:
    body: dict[str, Any] = {
        "url": cmd.browser_url,
        "headless": cmd.browser_headless,
    }
    if cmd.browser_session_id:
        body["session_id"] = cmd.browser_session_id
    if cmd.browser_title:
        body["title"] = cmd.browser_title
    if cmd.browser_engine:
        body["engine"] = cmd.browser_engine
    return "POST", "/session/browser/open", body


_STATIC_ROUTES: dict[CommandVerb, Callable[[CommandRequest], tuple[str, str, dict[str, Any] | None]]] = {
    CommandVerb.HEALTH: lambda _c: ("GET", "/health", None),
    CommandVerb.CAPABILITIES: lambda _c: ("GET", "/capabilities", None),
    CommandVerb.VIRTUAL_START: lambda c: (
        "POST",
        "/session/virtual/start",
        {"width": c.width, "height": c.height, "display": c.vd_display},
    ),
    CommandVerb.DIAGNOSE_CONTROL: lambda c: (
        "GET",
        f"/diagnostics/control{('?display=' + c.display) if c.display else ''}",
        None,
    ),
}

_CONTROL_VERBS = {
    CommandVerb.CONTROLS_LIST,
    CommandVerb.CONTROLS_FIND,
    CommandVerb.CONTROL_CLICK,
    CommandVerb.CONTROL_FOCUS,
    CommandVerb.CONTROL_SET_VALUE,
}


def route_command(cmd: CommandRequest) -> tuple[str, str, dict[str, Any] | None]:
    """Map CommandRequest to broker HTTP (method, path, body)."""
    verb = cmd.verb
    if verb in _STATIC_ROUTES:
        return _STATIC_ROUTES[verb](cmd)
    if verb in {CommandVerb.MONITORS, CommandVerb.OUTPUTS}:
        return _route_outputs_query(cmd)
    if verb == CommandVerb.WINDOWS:
        return _route_windows_query(cmd)
    if verb == CommandVerb.TERMINAL_OPEN:
        return _route_terminal_open(cmd)
    if verb == CommandVerb.BROWSER_OPEN:
        return _route_browser_open(cmd)
    if verb in _CONTROL_VERBS:
        from .application.handlers.control import control_request_body

        body = control_request_body(cmd)
        return _route_control_command(verb, body)
    raise VDisplayError(f"agent request has no direct route for verb: {verb.value}")


# Backward-compatible alias used by tests and internal callers.
_route_command = route_command

__all__ = ["route_command", "_route_command"]
