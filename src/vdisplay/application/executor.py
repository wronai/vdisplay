"""Execute CommandRequest via agent or local application services."""

from __future__ import annotations

import shutil
from typing import Any

from ..agent_config import resolve_agent_url
from ..client import AgentClient
from ..exceptions import VDisplayError
from .commands import CommandRequest, CommandResult, CommandVerb
from .errors import ApplicationError, ErrorCode, error_from_exception
from .runtime import ExecutionPolicy, Route, agent_client_required, get_execution_policy


def execute(
    cmd: CommandRequest,
    *,
    policy: ExecutionPolicy | None = None,
    force_route: Route | None = None,
) -> CommandResult:
    """Single entry for command execution across CLI, DSL, REST, and agent dispatch."""
    pol = policy or get_execution_policy()
    route = force_route or pol.route(cmd)
    meta = pol.meta_for(route)
    try:
        if route == "agent":
            data = _execute_agent(cmd)
            return CommandResult.success(action=cmd.action, data=data, command=cmd.line, meta=meta)
        data = _execute_local(cmd)
        return CommandResult.success(action=cmd.action, data=data, command=cmd.line, meta=meta)
    except VDisplayError as exc:
        return CommandResult.failure(
            action=cmd.action,
            error=error_from_exception(exc),
            command=cmd.line,
            meta=meta,
        )
    except Exception as exc:
        return CommandResult.failure(
            action=cmd.action,
            error=error_from_exception(exc),
            command=cmd.line,
            meta=meta,
        )


def _execute_local(cmd: CommandRequest) -> dict[str, Any]:
    from .services import capture, discovery, info, session

    verb = cmd.verb
    if verb == CommandVerb.HEALTH:
        return {"status": "ok"}
    if verb == CommandVerb.INFO:
        return info.platform_info()
    if verb in {CommandVerb.MONITORS, CommandVerb.OUTPUTS}:
        return discovery.list_monitors_local(cmd.display, include_all=cmd.include_all)
    if verb == CommandVerb.WINDOWS:
        return discovery.list_windows_local(
            cmd.display,
            include_all=cmd.include_all,
            apps_only=cmd.apps_only if cmd.apps_only else None,
            min_width=cmd.min_width,
            min_height=cmd.min_height,
            match_class=cmd.match_class,
            match_pid=cmd.match_pid,
            match_app=cmd.match_app,
        )
    if verb == CommandVerb.ALL:
        return discovery.list_all_local(
            cmd.display,
            include_all=cmd.include_all,
            match_class=cmd.match_class,
            match_pid=cmd.match_pid,
            match_app=cmd.match_app,
        )
    if verb == CommandVerb.CAPABILITIES:
        from ..api import MirrorSession, VirtualDisplaySession, WindowRelaySession

        return {
            "virtual": VirtualDisplaySession.create().capabilities(),
            "mirror": MirrorSession.create().capabilities(),
            "relay": WindowRelaySession.create().capabilities(),
        }
    if verb == CommandVerb.VALIDATE:
        tools = {
            "Xvfb": shutil.which("Xvfb"),
            "xwd": shutil.which("xwd"),
            "xrandr": shutil.which("xrandr"),
            "xdotool": shutil.which("xdotool"),
        }
        missing = [k for k, v in tools.items() if v is None]
        diag = discovery.diagnose(cmd.display)
        if missing:
            raise VDisplayError(f"missing tools: {', '.join(missing)}")
        return {"tools": tools, "missing": missing, "diagnostic": diag}
    if verb == CommandVerb.SCREENSHOT:
        return _screenshot_local(cmd, capture)
    if verb == CommandVerb.VIRTUAL_START:
        return session.virtual_start(
            width=cmd.width,
            height=cmd.height,
            backend=cmd.backend,
            display=cmd.vd_display,
        )
    if verb == CommandVerb.MIRROR:
        return session.mirror_start(
            source=cmd.source or "primary",
            target=cmd.target,
            display=cmd.display,
            output=cmd.output,
        )
    if verb == CommandVerb.ADOPT:
        return session.relay_adopt(
            display=cmd.display,
            match_title=cmd.match_title,
            window_id=cmd.window_id,
            match_class=cmd.match_class,
            match_pid=cmd.match_pid,
            match_app=cmd.match_app,
            target=cmd.target or "offscreen",
        )
    if verb == CommandVerb.RELEASE:
        return session.relay_release(
            display=cmd.display,
            match_title=cmd.match_title,
            window_id=cmd.window_id,
            match_class=cmd.match_class,
            match_pid=cmd.match_pid,
            match_app=cmd.match_app,
        )
    raise VDisplayError(f"unknown or unsupported verb: {verb.value}")


def _screenshot_local(cmd: CommandRequest, capture_module: Any) -> dict[str, Any]:
    from ..discovery import resolve_host_display

    display = str(cmd.display or ":99")
    host_display = resolve_host_display(None)
    mode = "virtual" if display != host_display else cmd.mode
    return capture_module.capture_screenshot_local(
        output=cmd.output or "screen.png",
        display=display if mode == "host" else None,
        monitor=cmd.monitor,
        source=cmd.source,
        target=cmd.target,
        mode=mode,
        all_monitors=cmd.all_monitors,
        out_dir=cmd.out_dir,
        width=cmd.width,
        height=cmd.height,
        vd_display=display if mode == "virtual" else cmd.vd_display,
    )


def _execute_agent(cmd: CommandRequest) -> dict[str, Any]:
    client = agent_client_required()
    verb = cmd.verb
    if verb == CommandVerb.HEALTH:
        return client.health()
    if verb == CommandVerb.INFO:
        caps = client.capabilities()
        return {
            "platform": {
                k: caps.get(k)
                for k in (
                    "platform",
                    "python",
                    "session_type",
                    "virtual_backend",
                    "mirror_backend",
                    "relay_backend",
                )
                if k in caps
            },
            "agent": caps,
        }
    if verb in {CommandVerb.MONITORS, CommandVerb.OUTPUTS}:
        payload = client.outputs(display=cmd.display, include_all=cmd.include_all)
        payload.pop("ok", None)
        return payload
    if verb == CommandVerb.WINDOWS:
        payload = client.windows(
            display=cmd.display,
            include_all=str(cmd.include_all).lower(),
            match_class=cmd.match_class,
            match_pid=cmd.match_pid,
            match_app=cmd.match_app,
        )
        payload.pop("ok", None)
        return payload
    if verb == CommandVerb.ALL:
        monitors = client.outputs(display=cmd.display, include_all=cmd.include_all)
        windows = client.windows(
            display=cmd.display,
            include_all=str(cmd.include_all).lower(),
            match_class=cmd.match_class,
            match_pid=cmd.match_pid,
            match_app=cmd.match_app,
        )
        monitors.pop("ok", None)
        windows.pop("ok", None)
        return {
            "requested_display": monitors.get("requested_display"),
            "resolved_display": monitors.get("resolved_display"),
            "monitor_count": monitors.get("monitor_count"),
            "window_count": windows.get("window_count"),
            "monitors": monitors.get("monitors"),
            "windows": windows.get("windows"),
        }
    if verb == CommandVerb.CAPABILITIES:
        payload = client.capabilities()
        payload.pop("ok", None)
        return payload
    if verb == CommandVerb.VALIDATE:
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
    if verb == CommandVerb.SCREENSHOT:
        return _screenshot_agent(cmd, client)
    if verb == CommandVerb.VIRTUAL_START:
        return client.start_virtual(
            width=cmd.width,
            height=cmd.height,
            display=cmd.vd_display,
        )
    if verb == CommandVerb.MIRROR:
        return _mirror_agent(cmd, client)
    if verb == CommandVerb.ADOPT:
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
    if verb == CommandVerb.RELEASE:
        relay = client.start_relay(display=cmd.display)
        return client.release_window(
            session_id=relay["session_id"],
            match_title=cmd.match_title,
            window_id=cmd.window_id,
            match_class=cmd.match_class,
            match_pid=cmd.match_pid,
            match_app=cmd.match_app,
        )
    raise VDisplayError(f"unknown verb: {verb.value}")


def _screenshot_agent(cmd: CommandRequest, client: AgentClient) -> dict[str, Any]:
    from .services import capture as capture_module
    from ..discovery import resolve_host_display

    display = str(cmd.display or ":99")
    host_display = resolve_host_display(None)
    mode = "virtual" if display != host_display else cmd.mode
    return capture_module.capture_screenshot_via_client(
        client,
        output=cmd.output or "screen.png",
        display=display if mode == "host" else None,
        mode=mode,
        vd_display=display if mode == "virtual" else cmd.vd_display,
        width=cmd.width,
        height=cmd.height,
        monitor=cmd.monitor,
        source=cmd.source,
        target=cmd.target,
        all_monitors=cmd.all_monitors,
        out_dir=cmd.out_dir,
    )


def _mirror_agent(cmd: CommandRequest, client: AgentClient) -> dict[str, Any]:
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
