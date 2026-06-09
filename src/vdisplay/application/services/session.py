"""Session use-cases: virtual, mirror, relay window operations."""

from __future__ import annotations

from typing import Any

from ...api import MirrorSession, VirtualDisplaySession, WindowRelaySession
from ...exceptions import VDisplayError


def virtual_start(
    *,
    width: int = 1920,
    height: int = 1080,
    backend: str = "xvfb",
    display: str = ":99",
) -> dict[str, Any]:
    session = VirtualDisplaySession.create(
        width=width,
        height=height,
        backend=backend,
        display=display,
    )
    session.start()
    return {"info": session.info(), "capabilities": session.capabilities()}


def virtual_launch(
    command: list[str],
    *,
    width: int = 1920,
    height: int = 1080,
    backend: str = "xvfb",
    display: str = ":99",
) -> dict[str, Any]:
    session = VirtualDisplaySession.create(
        width=width,
        height=height,
        backend=backend,
        display=display,
    )
    session.start()
    try:
        pid = session.launch(command)
        return {"pid": pid, "display": session.info()["metadata"]["display"]}
    finally:
        session.stop()


def virtual_screenshot(
    output: str,
    *,
    width: int = 1920,
    height: int = 1080,
    backend: str = "xvfb",
    display: str = ":99",
) -> dict[str, Any]:
    session = VirtualDisplaySession.create(
        width=width,
        height=height,
        backend=backend,
        display=display,
    )
    session.start()
    try:
        path = session.save_screenshot(output)
        return {"saved": path, "info": session.info()}
    finally:
        session.stop()


def mirror_start(
    *,
    source: str = "primary",
    target: str | None = None,
    backend: str = "x11",
    display: str | None = None,
    output: str | None = None,
) -> dict[str, Any]:
    session = MirrorSession.create(
        source=source,
        target=target,
        backend=backend,
        display=display,
    )
    session.start()
    try:
        payload: dict[str, Any] = {"info": session.info(), "capabilities": session.capabilities()}
        if output:
            payload["saved"] = session.save_screenshot(output)
        return payload
    finally:
        session.stop()


def mirror_screenshot(
    output: str,
    *,
    source: str = "primary",
    target: str | None = None,
    display: str | None = None,
) -> dict[str, Any]:
    from . import capture as capture_svc

    from ...capture.linux_xwd import _is_wayland_session

    # On Wayland, xrandr mirror sessions cannot drive-level screenshot; use ScreenCast crop.
    capture_mode = "host" if _is_wayland_session() else "mirror"
    meta = capture_svc.capture_screenshot(
        output=output,
        display=display,
        source=source,
        target=target,
        mode=capture_mode,
    )
    meta["info"] = MirrorSession.create(source=source, target=target, display=display).info()
    return meta


def relay_adopt(
    *,
    display: str | None = None,
    match_title: str | None = None,
    window_id: str | None = None,
    match_class: str | None = None,
    match_pid: int | None = None,
    match_app: str | None = None,
    target: str = "offscreen",
) -> dict[str, Any]:
    session = WindowRelaySession.create(display=display)
    session.start()
    try:
        wid = session.adopt_window(
            match_title=match_title,
            window_id=window_id,
            match_class=match_class,
            match_pid=match_pid,
            match_app=match_app,
            target=target,
        )
        return {"window_id": wid, "adopted": session.list_adopted()}
    finally:
        session.stop()


def relay_release(
    *,
    display: str | None = None,
    match_title: str | None = None,
    window_id: str | None = None,
    match_class: str | None = None,
    match_pid: int | None = None,
    match_app: str | None = None,
) -> dict[str, Any]:
    session = WindowRelaySession.create(display=display)
    session.start()
    try:
        wid = session.release_window(
            match_title=match_title,
            window_id=window_id,
            match_class=match_class,
            match_pid=match_pid,
            match_app=match_app,
        )
        return {"window_id": wid, "adopted": session.list_adopted()}
    finally:
        session.stop()


def relay_list_adopted(display: str | None = None) -> dict[str, Any]:
    session = WindowRelaySession.create(display=display)
    session.start()
    try:
        return {"adopted": session.list_adopted()}
    finally:
        session.stop()


def relay_screenshot(
    output: str,
    *,
    monitor: int = 1,
    display: str | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    from . import capture as capture_svc

    return capture_svc.capture_screenshot(
        output=output,
        monitor=monitor,
        display=display,
        source=source,
        mode="host",
    )


def unsupported_session_action(kind: str, action: str) -> None:
    raise VDisplayError(f"unsupported {kind} action: {action}")
