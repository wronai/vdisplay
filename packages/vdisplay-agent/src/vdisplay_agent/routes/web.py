"""Web console — multi-monitor view and automation controls."""

from __future__ import annotations

from collections.abc import Callable
from importlib import resources
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from .. import schemas as S
from ..envelope import json_error, json_from_runtime, strip_ok, success
from ..runtime import AgentRuntime
from ..services import web_console


def _console_html() -> str:
    path = Path(__file__).resolve().parent.parent / "static" / "console.html"
    if path.is_file():
        return path.read_text(encoding="utf-8")
    try:
        return resources.files("vdisplay_agent.static").joinpath("console.html").read_text(encoding="utf-8")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"console.html missing: {exc}") from exc


def register_routes(
    app: FastAPI,
    broker: AgentRuntime,
    check_auth: Callable[[str | None], None],
) -> None:
    @app.get("/web", response_class=HTMLResponse, include_in_schema=False)
    def web_console_page() -> HTMLResponse:
        return HTMLResponse(_console_html())

    @app.get("/api/web/overview")
    def web_overview(
        display: str | None = Query(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        check_auth(authorization)
        payload = web_console.build_overview(broker, display=display)
        return success(S.ACTION_WEB_OVERVIEW, payload)

    @app.get("/api/web/frame/{monitor_name}")
    def web_frame(
        monitor_name: str,
        display: str | None = Query(default=None),
        authorization: str | None = Header(default=None),
    ) -> FileResponse:
        check_auth(authorization)
        try:
            path = web_console.capture_monitor_frame(
                broker,
                monitor_name,
                display=display,
            )
        except Exception as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return FileResponse(path, media_type="image/png", filename=f"{monitor_name}.png")

    @app.get("/api/web/frames")
    def web_frames(
        display: str | None = Query(default=None),
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        try:
            frames = web_console.capture_all_monitor_frames(broker, display=display)
        except Exception as exc:
            return json_error(S.ACTION_WEB_FRAMES, exc)
        payload = {
            "count": len(frames),
            "frames": [
                {
                    "monitor_name": item["monitor_name"],
                    "url": f"/api/web/frame/{item['monitor_name']}",
                    "meta": item.get("meta"),
                }
                for item in frames
            ],
        }
        return json_from_runtime(S.ACTION_WEB_FRAMES, payload)

    @app.post("/api/web/screencast/start")
    async def web_screencast_start(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        payload = dict(body or {})
        payload.setdefault("multiple", True)
        payload.setdefault("interactive", True)
        try:
            return json_from_runtime(
                S.ACTION_SCREENCAST_START,
                broker.start_screencast(
                    interactive=bool(payload.get("interactive", True)),
                    timeout_s=float(payload.get("timeout_s", 120.0)),
                    multiple=payload.get("multiple"),
                ),
            )
        except Exception as exc:
            return json_error(S.ACTION_SCREENCAST_START, exc)

    @app.post("/api/web/sampler/start")
    async def web_sampler_start(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        payload = dict(body or {})
        payload.setdefault("mode", "desktop")
        payload.setdefault("all_monitors", True)
        payload.setdefault("interval_s", 5.0)
        try:
            return json_from_runtime(S.ACTION_SAMPLER_START, broker.start_sampler(payload))
        except Exception as exc:
            return json_error(S.ACTION_SAMPLER_START, exc)

    @app.get("/api/web/replay/sessions")
    def web_replay_sessions(
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        check_auth(authorization)
        return success(S.ACTION_WEB_REPLAY_SESSIONS, {"sessions": web_console.list_replay_sessions()})

    @app.post("/api/web/replay/start")
    async def web_replay_start(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        session_id = str((body or {}).get("session_id") or "").strip()
        if not session_id:
            return json_error(S.ACTION_WEB_REPLAY_START, ValueError("session_id required"))
        try:
            return json_from_runtime(S.ACTION_WEB_REPLAY_START, web_console.queue_replay(session_id))
        except Exception as exc:
            return json_error(S.ACTION_WEB_REPLAY_START, exc)

    @app.get("/api/web/replay/status/{job_id}")
    def web_replay_status(
        job_id: str,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        check_auth(authorization)
        from vdisplay.application.replay import replay_job_status

        payload = replay_job_status(job_id)
        if payload is None:
            raise HTTPException(status_code=404, detail=f"replay job not found: {job_id}")
        return success(S.ACTION_WEB_REPLAY_STATUS, payload)

    @app.post("/api/web/pointer/click")
    async def web_pointer_click(
        body: dict[str, Any],
        display: str | None = Query(default=None),
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        payload = dict(body or {})
        monitor_name = str(payload.get("monitor_name") or payload.get("monitor") or "").strip()
        if not monitor_name:
            return json_error(S.ACTION_WEB_POINTER_CLICK, ValueError("monitor_name required"))
        try:
            x = float(payload.get("x"))
            y = float(payload.get("y"))
        except (TypeError, ValueError):
            return json_error(S.ACTION_WEB_POINTER_CLICK, ValueError("x and y required"))
        coord_space = str(payload.get("coord_space") or "png")
        button = int(payload.get("button") or 1)
        try:
            return json_from_runtime(
                S.ACTION_WEB_POINTER_CLICK,
                web_console.click_monitor_pointer(
                    broker,
                    monitor_name=monitor_name,
                    x=x,
                    y=y,
                    coord_space=coord_space,
                    button=button,
                    display=display,
                ),
            )
        except Exception as exc:
            return json_error(S.ACTION_WEB_POINTER_CLICK, exc)
