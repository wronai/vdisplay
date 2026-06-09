from __future__ import annotations

import json
import shutil
from typing import Any

from dsl2vdisplay.result import DslResult


def handle_health(cmd: dict[str, Any], *, line: str) -> DslResult:
    return DslResult(ok=True, command=line, action="health", output="ok", data={"status": "ok"})


def handle_info(cmd: dict[str, Any], *, line: str) -> DslResult:
    from vdisplay.api import platform_summary
    from vdisplay import VirtualDisplaySession, MirrorSession, WindowRelaySession

    data = {
        "platform": platform_summary(),
        "virtual": VirtualDisplaySession.create().capabilities(),
        "mirror": MirrorSession.create().capabilities(),
        "relay": WindowRelaySession.create().capabilities(),
    }
    return DslResult(
        ok=True,
        command=line,
        action="info",
        output=json.dumps(data, indent=2),
        data=data,
    )


def handle_outputs(cmd: dict[str, Any], *, line: str) -> DslResult:
    from vdisplay.discovery import diagnose_display, list_outputs

    display = cmd.get("display")
    data = {"diagnostic": diagnose_display(display), "outputs": list_outputs(display)}
    return DslResult(
        ok=True,
        command=line,
        action="outputs",
        output=json.dumps(data, indent=2),
        data=data,
    )


def handle_windows(cmd: dict[str, Any], *, line: str) -> DslResult:
    from vdisplay.discovery import list_windows

    windows = list_windows(
        cmd.get("display"),
        apps_only=bool(cmd.get("apps_only", True)),
        match_class=cmd.get("class"),
        match_pid=cmd.get("pid"),
        match_app=cmd.get("app"),
    )
    return DslResult(
        ok=True,
        command=line,
        action="windows",
        output=json.dumps(windows, indent=2),
        data={"windows": windows},
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
    from vdisplay.discovery import diagnose_display

    tools = {
        "Xvfb": shutil.which("Xvfb"),
        "xwd": shutil.which("xwd"),
        "xrandr": shutil.which("xrandr"),
        "xdotool": shutil.which("xdotool"),
    }
    missing = [k for k, v in tools.items() if v is None]
    diag = diagnose_display(cmd.get("display"))
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
