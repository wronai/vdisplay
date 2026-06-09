"""Local REST API for vdisplay-agent (localhost-only broker)."""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse
from starlette.requests import Request

from . import schemas as S
from .envelope import json_error, json_from_runtime, strip_ok, success
from .runtime import AgentRuntime


def create_app(runtime: AgentRuntime | None = None):
    os.environ["VDISPLAY_AGENT_BROKER"] = "1"

    app = FastAPI(title="vdisplay-agent", version="0.1.0")
    broker = runtime or AgentRuntime()
    expected_token = (os.environ.get("VDISPLAY_AGENT_TOKEN") or "").strip()

    def _check_auth(authorization: str | None) -> None:
        if not expected_token:
            return
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="missing bearer token")
        if authorization.removeprefix("Bearer ").strip() != expected_token:
            raise HTTPException(status_code=403, detail="invalid bearer token")

    @app.get("/health")
    def health(authorization: str | None = Header(default=None)) -> dict[str, Any]:
        _check_auth(authorization)
        return success(
            S.ACTION_HEALTH,
            {"status": "ok", "service": "vdisplay-agent", "broker": "vdisplay-agent"},
        )

    @app.get("/capabilities")
    def capabilities(authorization: str | None = Header(default=None)) -> dict[str, Any]:
        _check_auth(authorization)
        return success(S.ACTION_CAPABILITIES, broker.platform_capabilities())

    @app.get("/diagnostics")
    def diagnostics(
        display: str | None = Query(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _check_auth(authorization)
        return success(S.ACTION_DIAGNOSTICS, broker.diagnostics(display=display))

    @app.get("/outputs")
    def outputs(
        display: str | None = Query(default=None),
        include_all: bool = Query(default=True),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _check_auth(authorization)
        return success(
            S.ACTION_OUTPUTS,
            broker.outputs(display=display, include_all=include_all),
        )

    @app.get("/windows")
    def windows(
        request: Request,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _check_auth(authorization)
        params = dict(request.query_params)
        return success(S.ACTION_WINDOWS, broker.list_windows(**params))

    @app.post("/session/virtual/start")
    async def session_virtual_start(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        _check_auth(authorization)
        try:
            return json_from_runtime(S.ACTION_VIRTUAL_START, broker.start_virtual(**body))
        except Exception as exc:
            return json_error(S.ACTION_VIRTUAL_START, exc)

    @app.post("/session/mirror/start")
    async def session_mirror_start(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        _check_auth(authorization)
        try:
            return json_from_runtime(S.ACTION_MIRROR_START, broker.start_mirror(**body))
        except Exception as exc:
            return json_error(S.ACTION_MIRROR_START, exc)

    @app.post("/session/relay/start")
    async def session_relay_start(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        _check_auth(authorization)
        try:
            return json_from_runtime(S.ACTION_RELAY_START, broker.start_relay(**body))
        except Exception as exc:
            return json_error(S.ACTION_RELAY_START, exc)

    @app.post("/session/screencast/start")
    async def session_screencast_start(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        _check_auth(authorization)
        try:
            return json_from_runtime(
                S.ACTION_SCREENCAST_START,
                broker.start_screencast(
                    interactive=bool(body.get("interactive", True)),
                    timeout_s=float(body.get("timeout_s", 120)),
                ),
            )
        except Exception as exc:
            return json_error(S.ACTION_SCREENCAST_START, exc)

    @app.post("/session/screencast/stop")
    def session_screencast_stop(
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        _check_auth(authorization)
        try:
            return json_from_runtime(S.ACTION_SCREENCAST_STOP, broker.stop_screencast())
        except Exception as exc:
            return json_error(S.ACTION_SCREENCAST_STOP, exc)

    @app.get("/session/screencast/status")
    def session_screencast_status(
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _check_auth(authorization)
        return success(S.ACTION_SCREENCAST_STATUS, strip_ok(broker.screencast_status()))

    @app.post("/session/{session_id}/stop")
    def session_stop(
        session_id: str,
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        _check_auth(authorization)
        try:
            return json_from_runtime(S.ACTION_SESSION_STOP, broker.stop_session(session_id))
        except Exception as exc:
            return json_error(S.ACTION_SESSION_STOP, exc)

    @app.post("/capture/frame")
    async def capture_frame(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        _check_auth(authorization)
        try:
            return json_from_runtime(S.ACTION_CAPTURE_FRAME, broker.capture_frame(body))
        except Exception as exc:
            return json_error(S.ACTION_CAPTURE_FRAME, exc)

    @app.post("/window/adopt")
    async def window_adopt(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        _check_auth(authorization)
        try:
            return json_from_runtime(S.ACTION_WINDOW_ADOPT, broker.adopt_window(body))
        except Exception as exc:
            return json_error(S.ACTION_WINDOW_ADOPT, exc)

    @app.post("/window/release")
    async def window_release(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        _check_auth(authorization)
        try:
            return json_from_runtime(S.ACTION_WINDOW_RELEASE, broker.release_window(body))
        except Exception as exc:
            return json_error(S.ACTION_WINDOW_RELEASE, exc)

    @app.on_event("shutdown")
    def _shutdown() -> None:
        broker.shutdown()

    app.state.runtime = broker
    return app
