from __future__ import annotations

import json
from typing import Any

from dsl2vdisplay.result import DslResult


def handle_screenshot(cmd: dict[str, Any], *, line: str) -> DslResult:
    from vdisplay import VirtualDisplaySession

    out = cmd.get("out", "screen.png")
    display = cmd.get("display", ":99")
    width = int(cmd.get("width", 1920))
    height = int(cmd.get("height", 1080))

    session = VirtualDisplaySession.create(width=width, height=height, display=display)
    session.start()
    try:
        path = session.save_screenshot(out)
        data = {"saved": path, "info": session.info()}
        return DslResult(ok=True, command=line, action="screenshot", output=json.dumps(data, indent=2), data=data)
    finally:
        session.stop()


def handle_virtual_start(cmd: dict[str, Any], *, line: str) -> DslResult:
    from vdisplay import VirtualDisplaySession

    display = cmd.get("display", ":99")
    width = int(cmd.get("width", 1920))
    height = int(cmd.get("height", 1080))
    session = VirtualDisplaySession.create(width=width, height=height, display=display)
    session.start()
    data = session.info()
    return DslResult(ok=True, command=line, action="virtual_start", output=json.dumps(data, indent=2), data=data)


def handle_mirror(cmd: dict[str, Any], *, line: str) -> DslResult:
    from vdisplay import MirrorSession
    from vdisplay.discovery import list_outputs, resolve_host_display

    display = resolve_host_display(cmd.get("display"))
    source = cmd.get("source", "primary")
    target = cmd.get("target")
    outputs = list_outputs(display)
    if len(outputs) < 2:
        return DslResult(
            ok=False,
            command=line,
            action="mirror",
            error=f"mirror needs 2+ outputs on {display}, found {len(outputs)}",
            data={"outputs": outputs},
        )

    session = MirrorSession.create(source=source, target=target, display=display)
    session.start()
    try:
        data: dict[str, Any] = {"info": session.info()}
        if out := cmd.get("out"):
            data["saved"] = session.save_screenshot(out)
        return DslResult(ok=True, command=line, action="mirror", output=json.dumps(data, indent=2), data=data)
    finally:
        session.stop()


def handle_adopt(cmd: dict[str, Any], *, line: str) -> DslResult:
    from vdisplay import WindowRelaySession
    from vdisplay.discovery import resolve_host_display

    session = WindowRelaySession.create(display=resolve_host_display(cmd.get("display")))
    session.start()
    try:
        wid = session.adopt_window(
            match_title=cmd.get("title"),
            window_id=cmd.get("window_id"),
            target=cmd.get("target", "offscreen"),
        )
        data = {"window_id": wid, "adopted": session.list_adopted()}
        return DslResult(ok=True, command=line, action="adopt", output=json.dumps(data, indent=2), data=data)
    finally:
        session.stop()


def handle_release(cmd: dict[str, Any], *, line: str) -> DslResult:
    from vdisplay import WindowRelaySession
    from vdisplay.discovery import resolve_host_display

    session = WindowRelaySession.create(display=resolve_host_display(cmd.get("display")))
    session.start()
    try:
        wid = session.release_window(
            match_title=cmd.get("title"),
            window_id=cmd.get("window_id"),
            match_class=cmd.get("class"),
            match_pid=cmd.get("pid"),
            match_app=cmd.get("app"),
        )
        data = {"window_id": wid, "adopted": session.list_adopted()}
        return DslResult(ok=True, command=line, action="release", output=json.dumps(data, indent=2), data=data)
    finally:
        session.stop()
