"""Background frame sampler in the broker process."""

from __future__ import annotations

from typing import Any

from vdisplay import VirtualDisplaySession
from vdisplay.application.services.sampler_loop import SamplerLoop, SamplerLoopConfig
from vdisplay.capture.host import capture_host_to_file
from vdisplay.exceptions import VDisplayError

from ..session_store import SessionStore
from ..task_store import TaskStore
from . import tasks as task_svc


def _config_from_body(body: dict[str, Any]) -> SamplerLoopConfig:
    fmt = str(body.get("format") or "png").lower()
    if fmt not in {"png", "webp", "jpeg", "jpg"}:
        raise VDisplayError(f"unsupported sampler format: {fmt}")
    if fmt == "jpg":
        fmt = "jpeg"
    return SamplerLoopConfig(
        interval_s=float(body.get("interval_s") or body.get("interval") or 1.0),
        mode=str(body.get("mode") or "desktop"),
        source=body.get("source"),
        display=body.get("display"),
        vd_display=str(body.get("vd_display") or ":99"),
        output_dir=str(body.get("out_dir") or body.get("output_dir") or "./captures"),
        max_frames=body.get("max_frames"),
        dedupe=bool(body.get("dedupe", True)),
        width=int(body.get("width") or 1280),
        height=int(body.get("height") or 720),
        format=fmt,  # type: ignore[arg-type]
    )


def _ensure_virtual_session(
    store: SessionStore,
    *,
    vd_display: str,
    width: int,
    height: int,
) -> VirtualDisplaySession:
    key = (vd_display, width, height)
    if store.virtual is not None and store.virtual_key == key:
        if store.virtual.info().get("active"):
            return store.virtual
        store.virtual.stop()
        store.virtual = None
        store.virtual_key = None

    session = VirtualDisplaySession.create(width=width, height=height, display=vd_display)
    session.start()
    store.virtual = session
    store.virtual_key = key
    return session


def _capture_virtual_persistent(store: SessionStore, **kwargs: Any) -> dict[str, Any]:
    output = kwargs.get("output")
    if not output:
        raise VDisplayError("sampler capture requires output path")
    session = _ensure_virtual_session(
        store,
        vd_display=str(kwargs.get("vd_display") or ":99"),
        width=int(kwargs.get("width") or 1280),
        height=int(kwargs.get("height") or 720),
    )
    path = session.save_screenshot(str(output))
    return {
        "path": path,
        "mode": "virtual",
        "method": "virtual-xvfb",
        "info": session.info(),
    }


def _recover_screencast(store: SessionStore) -> bool:
    from vdisplay.capture.portal_screencast import (
        get_active_screencast,
        invalidate_screencast_session,
        start_screencast_session,
    )

    session = store.screencast or get_active_screencast()
    invalidate_screencast_session(session)
    store.screencast = None
    try:
        new_session = start_screencast_session(
            interactive=False,
            timeout_s=30.0,
            multiple=store.screencast_multiple,
        )
    except VDisplayError:
        return False
    store.screencast = new_session
    return new_session.is_ready


def start_sampler(
    store: SessionStore,
    body: dict[str, Any],
    *,
    task_store: TaskStore | None = None,
    broker_id: str = "",
) -> dict[str, Any]:
    if store.sampler is not None and store.sampler.state.running:
        raise VDisplayError("sampler already running — POST /sampler/stop first")

    config = _config_from_body(body)

    def capture_fn(**kwargs: Any) -> dict[str, Any]:
        output = kwargs.get("output")
        if not output:
            raise VDisplayError("sampler capture requires output path")
        if kwargs.get("mode") == "virtual":
            return _capture_virtual_persistent(store, **kwargs)
        return capture_host_to_file(
            output,
            monitor=1,
            display=kwargs.get("display"),
            source=kwargs.get("source"),
            prefer_mirror=False,
            screencast_session=store.screencast,
        )

    screencast_ready = store.screencast is not None and store.screencast.is_ready
    recover_fn = _recover_screencast if config.mode in {"desktop", "unattended"} else None
    loop = SamplerLoop(
        config,
        capture_fn,
        screencast_ready=screencast_ready,
        recover_fn=recover_fn,
    )
    store.sampler = loop
    payload = loop.start()
    if task_store is not None and broker_id:
        store.sampler_task_id = task_svc.begin_sampler_task(
            task_store,
            broker_id=broker_id,
            config=config,
        )
        payload["task_id"] = store.sampler_task_id
        task_svc.touch_sampler_task(
            task_store,
            store.sampler_task_id,
            broker_id=broker_id,
            state=payload,
        )
    return payload


def stop_sampler(store: SessionStore, *, task_store: TaskStore | None = None) -> dict[str, Any]:
    if store.sampler is None:
        return {"ok": True, "running": False, "stopped": False}
    payload = store.sampler.stop()
    if task_store is not None and store.sampler_task_id:
        task_svc.end_sampler_task(task_store, store.sampler_task_id, state=payload)
        store.sampler_task_id = None
    store.sampler = None
    payload["stopped"] = True
    return payload


def sampler_status(
    store: SessionStore,
    *,
    task_store: TaskStore | None = None,
    broker_id: str = "",
) -> dict[str, Any]:
    if store.sampler is None:
        return {"ok": True, "running": False}
    payload = store.sampler.status()
    if task_store is not None and store.sampler_task_id and broker_id:
        task_svc.touch_sampler_task(
            task_store,
            store.sampler_task_id,
            broker_id=broker_id,
            state=payload,
        )
        payload["task_id"] = store.sampler_task_id
    return payload
