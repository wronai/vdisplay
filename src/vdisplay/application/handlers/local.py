"""Local (in-process) command handlers."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from typing import Any

from ...exceptions import VDisplayError
from ..commands import CommandRequest, CommandVerb

LocalHandler = Callable[[CommandRequest], dict[str, Any]]


def _health(_cmd: CommandRequest) -> dict[str, Any]:
    return {"status": "ok"}


def _info(_cmd: CommandRequest) -> dict[str, Any]:
    from ..services import info

    return info.platform_info()


def _monitors(cmd: CommandRequest) -> dict[str, Any]:
    from ..services import discovery

    return discovery.list_monitors_local(cmd.display, include_all=cmd.include_all)


def _windows(cmd: CommandRequest) -> dict[str, Any]:
    from ..services import discovery

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


def _all(cmd: CommandRequest) -> dict[str, Any]:
    from ..services import discovery

    return discovery.list_all_local(
        cmd.display,
        include_all=cmd.include_all,
        match_class=cmd.match_class,
        match_pid=cmd.match_pid,
        match_app=cmd.match_app,
    )


def _capabilities(_cmd: CommandRequest) -> dict[str, Any]:
    from ...api import MirrorSession, VirtualDisplaySession, WindowRelaySession

    return {
        "virtual": VirtualDisplaySession.create().capabilities(),
        "mirror": MirrorSession.create().capabilities(),
        "relay": WindowRelaySession.create().capabilities(),
    }


def _validate(cmd: CommandRequest) -> dict[str, Any]:
    from ..services import discovery

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


def _screenshot(cmd: CommandRequest) -> dict[str, Any]:
    from ..services import capture

    mode, display, vd_display = capture.resolve_screenshot_routing(cmd)
    return capture.capture_screenshot_local(
        output=cmd.output or "screen.png",
        display=None if mode == "virtual" else display,
        monitor=cmd.monitor,
        source=cmd.source,
        target=cmd.target,
        mode=mode,
        all_monitors=cmd.all_monitors,
        out_dir=cmd.out_dir,
        width=cmd.width,
        height=cmd.height,
        vd_display=vd_display,
    )


def _virtual_start(cmd: CommandRequest) -> dict[str, Any]:
    from ..services import session

    return session.virtual_start(
        width=cmd.width,
        height=cmd.height,
        backend=cmd.backend,
        display=cmd.vd_display,
    )


def _mirror(cmd: CommandRequest) -> dict[str, Any]:
    from ..services import session

    return session.mirror_start(
        source=cmd.source or "primary",
        target=cmd.target,
        display=cmd.display,
        output=cmd.output,
    )


def _adopt(cmd: CommandRequest) -> dict[str, Any]:
    from ..services import session

    return session.relay_adopt(
        display=cmd.display,
        match_title=cmd.match_title,
        window_id=cmd.window_id,
        match_class=cmd.match_class,
        match_pid=cmd.match_pid,
        match_app=cmd.match_app,
        target=cmd.target or "offscreen",
    )


def _release(cmd: CommandRequest) -> dict[str, Any]:
    from ..services import session

    return session.relay_release(
        display=cmd.display,
        match_title=cmd.match_title,
        window_id=cmd.window_id,
        match_class=cmd.match_class,
        match_pid=cmd.match_pid,
        match_app=cmd.match_app,
    )


_LOCAL_HANDLERS: dict[CommandVerb, LocalHandler] = {
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
    CommandVerb.MIRROR: _mirror,
    CommandVerb.ADOPT: _adopt,
    CommandVerb.RELEASE: _release,
}


def execute_local(cmd: CommandRequest) -> dict[str, Any]:
    handler = _LOCAL_HANDLERS.get(cmd.verb)
    if handler is None:
        raise VDisplayError(f"unknown or unsupported verb: {cmd.verb.value}")
    return handler(cmd)
