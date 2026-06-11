"""Agent-broker command handlers."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from typing import Any

from ...agent_config import resolve_agent_url
from ...client import AgentClient
from ...exceptions import VDisplayError
from ..commands import CommandRequest, CommandVerb
from ..runtime import agent_client_required
from ..session_context import bind_audit_command

AgentHandler = Callable[[AgentClient, CommandRequest], dict[str, Any]]

_INFO_KEYS = (
    "platform",
    "python",
    "session_type",
    "virtual_backend",
    "mirror_backend",
    "relay_backend",
)


def _strip_ok(payload: dict[str, Any]) -> dict[str, Any]:
    data = dict(payload)
    data.pop("ok", None)
    return data


def _require_agent_data(client: AgentClient, cmd: CommandRequest) -> dict[str, Any]:
    result = client.request(cmd)
    if not result.ok:
        message = result.error.message if result.error else "agent request failed"
        raise VDisplayError(message)
    return dict(result.data or {})


def _health(client: AgentClient, cmd: CommandRequest) -> dict[str, Any]:
    return _require_agent_data(client, cmd)


def _info(client: AgentClient, _cmd: CommandRequest) -> dict[str, Any]:
    caps = client.capabilities()
    return {
        "platform": {k: caps.get(k) for k in _INFO_KEYS if k in caps},
        "agent": caps,
    }


def _monitors(client: AgentClient, cmd: CommandRequest) -> dict[str, Any]:
    return _strip_ok(_require_agent_data(client, cmd))


def _windows(client: AgentClient, cmd: CommandRequest) -> dict[str, Any]:
    return _strip_ok(_require_agent_data(client, cmd))


def _all(client: AgentClient, cmd: CommandRequest) -> dict[str, Any]:
    from ..services.discovery import list_adopted

    monitors = client.outputs(display=cmd.display, include_all=cmd.include_all)
    windows = client.windows(
        display=cmd.display,
        include_all=str(cmd.include_all).lower(),
        match_class=cmd.match_class,
        match_pid=cmd.match_pid,
        match_app=cmd.match_app,
        min_width=cmd.min_width or None,
        min_height=cmd.min_height or None,
    )
    adopted = list_adopted(cmd.display)
    return {
        "requested_display": monitors.get("requested_display"),
        "resolved_display": monitors.get("resolved_display"),
        "monitor_count": monitors.get("monitor_count"),
        "window_count": windows.get("window_count"),
        "adopted_count": len(adopted),
        "monitors": monitors.get("monitors"),
        "windows": windows.get("windows"),
        "adopted": adopted,
    }


def _capabilities(client: AgentClient, cmd: CommandRequest) -> dict[str, Any]:
    return _strip_ok(_require_agent_data(client, cmd))


def _validate(client: AgentClient, cmd: CommandRequest) -> dict[str, Any]:
    diag = client.diagnostics(display=cmd.display)
    tools = {
        "Xvfb": shutil.which("Xvfb"),
        "xwd": shutil.which("xwd"),
        "xrandr": shutil.which("xrandr"),
        "xdotool": shutil.which("xdotool"),
    }
    missing = [k for k, v in tools.items() if v is None]
    if missing:
        raise VDisplayError(f"missing tools: {', '.join(missing)}")
    return {
        "tools": tools,
        "missing": missing,
        "diagnostic": diag,
        "agent_url": resolve_agent_url(),
    }


def _screenshot(client: AgentClient, cmd: CommandRequest) -> dict[str, Any]:
    from ..services import capture

    mode, display, vd_display = capture.resolve_screenshot_routing(cmd)
    return capture.capture_screenshot_via_client(
        client,
        output=cmd.output or "screen.png",
        display=None if mode == "virtual" else display,
        mode=mode,
        vd_display=vd_display,
        width=cmd.width,
        height=cmd.height,
        monitor=cmd.monitor,
        source=cmd.source,
        target=cmd.target,
        all_monitors=cmd.all_monitors,
        out_dir=cmd.out_dir,
    )


def _virtual_start(client: AgentClient, cmd: CommandRequest) -> dict[str, Any]:
    return _require_agent_data(client, cmd)


def _terminal_open(client: AgentClient, cmd: CommandRequest) -> dict[str, Any]:
    return _require_agent_data(client, cmd)


def _browser_open(client: AgentClient, cmd: CommandRequest) -> dict[str, Any]:
    return _require_agent_data(client, cmd)


def _mirror(client: AgentClient, cmd: CommandRequest) -> dict[str, Any]:
    source = cmd.source or "primary"
    monitors = client.outputs(display=cmd.display)
    if int(monitors.get("monitor_count") or 0) < 2:
        raise VDisplayError(f"mirror needs 2+ outputs, found {monitors.get('monitor_count')}")
    started = client.start_mirror(source=source, target=cmd.target, display=cmd.display)
    session_id = started["session_id"]
    try:
        data: dict[str, Any] = {"info": started.get("info"), "session_id": session_id}
        if cmd.output:
            shot = client.capture_frame(session_id=session_id, output=cmd.output)
            shot.pop("png_base64", None)
            data["saved"] = shot.get("path") or cmd.output
        return data
    finally:
        client.stop_session(session_id)


def _adopt(client: AgentClient, cmd: CommandRequest) -> dict[str, Any]:
    relay = client.start_relay(display=cmd.display)
    return client.adopt_window(
        session_id=relay["session_id"],
        match_title=cmd.match_title,
        window_id=cmd.window_id,
        match_class=cmd.match_class,
        match_pid=cmd.match_pid,
        match_app=cmd.match_app,
        target=cmd.target or "offscreen",
    )


def _release(client: AgentClient, cmd: CommandRequest) -> dict[str, Any]:
    relay = client.start_relay(display=cmd.display)
    return client.release_window(
        session_id=relay["session_id"],
        match_title=cmd.match_title,
        window_id=cmd.window_id,
        match_class=cmd.match_class,
        match_pid=cmd.match_pid,
        match_app=cmd.match_app,
    )


def _diagnose_control(client: AgentClient, cmd: CommandRequest) -> dict[str, Any]:
    return _strip_ok(client.diagnose_control(display=cmd.display))


def _controls_list(client: AgentClient, cmd: CommandRequest) -> dict[str, Any]:
    from .control import control_request_body

    return _strip_ok(client.list_controls(control_request_body(cmd)))


def _controls_find(client: AgentClient, cmd: CommandRequest) -> dict[str, Any]:
    from .control import control_request_body

    return _strip_ok(client.find_controls(control_request_body(cmd)))


def _control_click(client: AgentClient, cmd: CommandRequest) -> dict[str, Any]:
    from .control import control_request_body

    return _strip_ok(client.invoke_control(control_request_body(cmd)))


def _control_focus(client: AgentClient, cmd: CommandRequest) -> dict[str, Any]:
    from .control import control_request_body

    return _strip_ok(client.focus_control(control_request_body(cmd)))


def _control_set_value(client: AgentClient, cmd: CommandRequest) -> dict[str, Any]:
    from .control import control_request_body

    return _strip_ok(client.set_control_value(control_request_body(cmd)))


_AGENT_HANDLERS: dict[CommandVerb, AgentHandler] = {
    CommandVerb.HEALTH: _health,
    CommandVerb.INFO: _info,
    CommandVerb.MONITORS: _monitors,
    CommandVerb.OUTPUTS: _monitors,
    CommandVerb.WINDOWS: _windows,
    CommandVerb.ALL: _all,
    CommandVerb.CAPABILITIES: _capabilities,
    CommandVerb.VALIDATE: _validate,
    CommandVerb.SCREENSHOT: _screenshot,
    CommandVerb.VIRTUAL_START: _virtual_start,
    CommandVerb.TERMINAL_OPEN: _terminal_open,
    CommandVerb.BROWSER_OPEN: _browser_open,
    CommandVerb.MIRROR: _mirror,
    CommandVerb.ADOPT: _adopt,
    CommandVerb.RELEASE: _release,
    CommandVerb.DIAGNOSE_CONTROL: _diagnose_control,
    CommandVerb.CONTROLS_LIST: _controls_list,
    CommandVerb.CONTROLS_FIND: _controls_find,
    CommandVerb.CONTROL_CLICK: _control_click,
    CommandVerb.CONTROL_FOCUS: _control_focus,
    CommandVerb.CONTROL_SET_VALUE: _control_set_value,
}


def execute_agent(cmd: CommandRequest) -> dict[str, Any]:
    client = agent_client_required()
    handler = _AGENT_HANDLERS.get(cmd.verb)
    if handler is None:
        raise VDisplayError(f"unknown verb: {cmd.verb.value}")
    with bind_audit_command(cmd):
        return handler(client, cmd)
