from __future__ import annotations

import json
from typing import Any

from dsl2vdisplay.result import DslResult


def _ok(line: str, action: str, data: dict[str, Any]) -> DslResult:
    return DslResult(
        ok=True,
        command=line,
        action=action,
        output=json.dumps(data, indent=2, ensure_ascii=False),
        data=data,
    )


def _err(line: str, action: str, error: str, data: dict[str, Any] | None = None) -> DslResult:
    return DslResult(
        ok=False,
        command=line,
        action=action,
        error=error,
        data=data or {},
    )


def handle_screenshot(cmd: dict[str, Any], *, line: str) -> DslResult:
    from vdisplay.application.services import capture

    display = cmd.get("display", ":99")
    try:
        data = capture.capture_screenshot(
            output=cmd.get("out", "screen.png"),
            mode="virtual",
            vd_display=display,
            width=int(cmd.get("width", 1920)),
            height=int(cmd.get("height", 1080)),
        )
    except Exception as exc:
        return _err(line, "screenshot", str(exc))
    return _ok(line, "screenshot", data)


def handle_virtual_start(cmd: dict[str, Any], *, line: str) -> DslResult:
    from vdisplay.application.services import session

    try:
        data = session.virtual_start(
            display=cmd.get("display", ":99"),
            width=int(cmd.get("width", 1920)),
            height=int(cmd.get("height", 1080)),
        )
    except Exception as exc:
        return _err(line, "virtual_start", str(exc))
    return _ok(line, "virtual_start", data.get("info", data))


def handle_mirror(cmd: dict[str, Any], *, line: str) -> DslResult:
    from vdisplay.application.services import session
    from vdisplay.discovery import list_outputs, resolve_host_display

    display = resolve_host_display(cmd.get("display"))
    outputs = list_outputs(display)
    if len(outputs) < 2:
        return _err(
            line,
            "mirror",
            f"mirror needs 2+ outputs on {display}, found {len(outputs)}",
            {"outputs": outputs},
        )

    try:
        data = session.mirror_start(
            source=cmd.get("source", "primary"),
            target=cmd.get("target"),
            display=display,
            output=cmd.get("out"),
        )
    except Exception as exc:
        return _err(line, "mirror", str(exc))
    return _ok(line, "mirror", data)


def handle_adopt(cmd: dict[str, Any], *, line: str) -> DslResult:
    from vdisplay.application.services import session
    from vdisplay.discovery import resolve_host_display

    try:
        data = session.relay_adopt(
            display=resolve_host_display(cmd.get("display")),
            match_title=cmd.get("title"),
            window_id=cmd.get("window_id"),
            match_class=cmd.get("class"),
            match_pid=int(cmd["pid"]) if cmd.get("pid") is not None else None,
            match_app=cmd.get("app"),
            target=cmd.get("target", "offscreen"),
        )
    except Exception as exc:
        return _err(line, "adopt", str(exc))
    return _ok(line, "adopt", data)


def handle_release(cmd: dict[str, Any], *, line: str) -> DslResult:
    from vdisplay.application.services import session
    from vdisplay.discovery import resolve_host_display

    try:
        data = session.relay_release(
            display=resolve_host_display(cmd.get("display")),
            match_title=cmd.get("title"),
            window_id=cmd.get("window_id"),
            match_class=cmd.get("class"),
            match_pid=int(cmd["pid"]) if cmd.get("pid") is not None else None,
            match_app=cmd.get("app"),
        )
    except Exception as exc:
        return _err(line, "release", str(exc))
    return _ok(line, "release", data)
