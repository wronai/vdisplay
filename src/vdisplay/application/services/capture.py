"""Screenshot / frame capture use-cases."""

from __future__ import annotations

from typing import Any

from ...api import VirtualDisplaySession
from ...exceptions import VDisplayError
from ..commands import CommandRequest, CommandVerb


def resolve_screenshot_routing(cmd: CommandRequest) -> tuple[str, str | None, str]:
    """Return (mode, display, vd_display) for host vs virtual capture."""
    from ...discovery import resolve_host_display

    host_display = resolve_host_display(None)

    if cmd.mode == "virtual":
        return "virtual", None, cmd.vd_display or cmd.display or ":99"

    if cmd.display is not None and cmd.display != host_display:
        return "virtual", None, cmd.display

    return cmd.mode, cmd.display or host_display, cmd.vd_display


def capture_screenshot(
    *,
    output: str | None = None,
    display: str | None = None,
    monitor: int | None = None,
    source: str | None = None,
    target: str | None = None,
    mode: str = "host",
    all_monitors: bool = False,
    out_dir: str | None = None,
    width: int = 1280,
    height: int = 720,
    vd_display: str = ":99",
    skip_img2nl: bool = False,
) -> dict[str, Any]:
    from ..executor import execute

    result = execute(
        CommandRequest(
            verb=CommandVerb.SCREENSHOT,
            output=output,
            display=display,
            monitor=monitor,
            source=source,
            target=target,
            mode=mode,
            all_monitors=all_monitors,
            out_dir=out_dir,
            width=width,
            height=height,
            vd_display=vd_display,
            extra={"skip_img2nl": skip_img2nl},
        )
    )
    if not result.ok:
        message = result.error.message if result.error else "screenshot failed"
        raise VDisplayError(message)
    return result.data


def capture_screenshot_local(
    *,
    output: str | None = None,
    display: str | None = None,
    monitor: int | None = None,
    source: str | None = None,
    target: str | None = None,
    mode: str = "host",
    all_monitors: bool = False,
    out_dir: str | None = None,
    width: int = 1280,
    height: int = 720,
    vd_display: str = ":99",
) -> dict[str, Any]:
    from ...capture.host import capture_all_monitors, capture_host_to_file

    if mode == "virtual":
        session = VirtualDisplaySession.create(width=width, height=height, display=vd_display)
        session.start()
        try:
            out = output or "screen.png"
            path = session.save_screenshot(out)
            return {"saved": path, "mode": "virtual", "info": session.info()}
        finally:
            session.stop()

    if all_monitors:
        directory = out_dir or "."
        bulk = capture_all_monitors(
            display=display,
            out_dir=directory,
            target=target,
            prefer_mirror=mode == "mirror",
        )
        return {"mode": mode, "out_dir": str(directory), **bulk}

    if not output:
        raise VDisplayError("screenshot requires -o/--output (or use --all-monitors --out-dir)")

    meta = capture_host_to_file(
        output,
        monitor=monitor or 1,
        display=display,
        source=source,
        target=target,
        prefer_mirror=mode == "mirror",
    )
    meta["mode"] = mode
    return meta


def _ensure_wayland_screencast(client) -> None:
    from ...capture.linux_xwd import _is_wayland_session

    if not _is_wayland_session():
        return
    status = client.screencast_status()
    if status.get("active") and status.get("ready"):
        return
    import sys

    print(
        "vdisplay: starting ScreenCast — in the GNOME portal choose All Screens",
        file=sys.stderr,
    )
    from .screencast_cli import start_screencast_via_agent

    started = start_screencast_via_agent(
        client,
        interactive=True,
        timeout_s=120.0,
        multiple=True,
    )
    if not (started.get("active") and started.get("ready")):
        raise VDisplayError(
            f"screencast start failed: {started.get('error') or started}. "
            "Run: vdisplay agent screencast start"
        )


def _capture_via_agent(
    client,
    *,
    output: str | None,
    display: str | None,
    monitor: int | None,
    source: str | None,
    target: str | None,
    mode: str,
    all_monitors: bool,
    out_dir: str | None,
    width: int,
    height: int,
    vd_display: str,
) -> dict[str, Any]:
    if mode == "virtual":
        started = client.start_virtual(width=width, height=height, display=vd_display)
        session_id = started.get("session_id")
        if not session_id:
            raise VDisplayError(
                "agent virtual start response missing session_id "
                f"(keys={sorted(started)})"
            )
        try:
            out = output or "screen.png"
            payload = client.capture_frame(session_id=session_id, output=out)
            payload.pop("png_base64", None)
            payload["saved"] = payload.get("path") or out
            payload["mode"] = "virtual"
            payload["info"] = started.get("info")
            return payload
        finally:
            client.stop_session(session_id)

    _ensure_wayland_screencast(client)

    if all_monitors:
        directory = out_dir or "."
        payload = client.capture_frame(
            display=display,
            target=target,
            prefer_mirror=mode == "mirror",
            all_monitors=True,
            out_dir=directory,
        )
        payload["mode"] = mode
        return payload

    if not output:
        raise VDisplayError("screenshot requires -o/--output (or use --all-monitors --out-dir)")

    payload = client.capture_frame(
        output=output,
        monitor=monitor or 1,
        display=display,
        source=source,
        target=target,
        prefer_mirror=mode == "mirror",
    )
    payload.pop("png_base64", None)
    payload["mode"] = mode
    return payload


def capture_screenshot_via_client(client, **kwargs: Any) -> dict[str, Any]:
    """Agent client path — shared by executor and legacy agent_dispatch."""
    return _capture_via_agent(client, **kwargs)
