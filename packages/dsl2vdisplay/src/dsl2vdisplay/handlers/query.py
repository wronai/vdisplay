from __future__ import annotations

import json
import shutil
from typing import Any

from dsl2vdisplay.result import DslResult


def handle_health(cmd: dict[str, Any], *, line: str) -> DslResult:
    return DslResult(ok=True, command=line, action="health", output="ok", data={"status": "ok"})


def handle_info(cmd: dict[str, Any], *, line: str) -> DslResult:
    from vdisplay.application.services import info as info_service

    data = info_service.platform_info()
    return DslResult(
        ok=True,
        command=line,
        action="info",
        output=json.dumps(data, indent=2),
        data=data,
    )


def handle_monitors(cmd: dict[str, Any], *, line: str) -> DslResult:
    from vdisplay.application.services import discovery

    data = discovery.list_monitors(cmd.get("display"), include_all=not bool(cmd.get("apps_only", False)))
    return DslResult(
        ok=True,
        command=line,
        action="monitors",
        output=json.dumps(data, indent=2),
        data=data,
    )


def handle_outputs(cmd: dict[str, Any], *, line: str) -> DslResult:
    result = handle_monitors(cmd, line=line)
    result.action = "outputs"
    return result


def handle_windows(cmd: dict[str, Any], *, line: str) -> DslResult:
    from vdisplay.application.services import discovery

    data = discovery.list_windows_payload(
        cmd.get("display"),
        include_all=not bool(cmd.get("apps_only", False)),
        match_class=cmd.get("class"),
        match_pid=cmd.get("pid"),
        match_app=cmd.get("app"),
    )
    return DslResult(
        ok=True,
        command=line,
        action="windows",
        output=json.dumps(data, indent=2),
        data=data,
    )


def handle_all(cmd: dict[str, Any], *, line: str) -> DslResult:
    from vdisplay.application.services import discovery

    data = discovery.list_all(
        cmd.get("display"),
        include_all=not bool(cmd.get("apps_only", False)),
        match_class=cmd.get("class"),
        match_pid=cmd.get("pid"),
        match_app=cmd.get("app"),
    )
    return DslResult(
        ok=True,
        command=line,
        action="all",
        output=json.dumps(data, indent=2),
        data=data,
    )


def handle_capabilities(cmd: dict[str, Any], *, line: str) -> DslResult:
    from vdisplay import VirtualDisplaySession, MirrorSession, WindowRelaySession

    data = {
        "virtual": VirtualDisplaySession.create().capabilities(),
        "mirror": MirrorSession.create().capabilities(),
        "relay": WindowRelaySession.create().capabilities(),
    }
    return DslResult(ok=True, command=line, action="capabilities", output=json.dumps(data, indent=2), data=data)


def handle_validate(cmd: dict[str, Any], *, line: str) -> DslResult:
    from vdisplay.application.services import discovery

    tools = {
        "Xvfb": shutil.which("Xvfb"),
        "xwd": shutil.which("xwd"),
        "xrandr": shutil.which("xrandr"),
        "xdotool": shutil.which("xdotool"),
    }
    missing = [k for k, v in tools.items() if v is None]
    diag = discovery.diagnose(cmd.get("display"))
    ok = not missing
    data = {"tools": tools, "missing": missing, "diagnostic": diag}
    return DslResult(
        ok=ok,
        command=line,
        action="validate",
        output=json.dumps(data, indent=2),
        data=data,
        error=None if ok else f"missing tools: {', '.join(missing)}",
    )
