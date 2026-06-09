"""Virtual, mirror, relay, and screencast session routes."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse

from .. import schemas as S
from ..envelope import json_error, json_from_runtime, strip_ok, success
from ..runtime import AgentRuntime


def register_routes(
    app: FastAPI,
    broker: AgentRuntime,
    check_auth: Callable[[str | None], None],
) -> None:
    @app.post("/session/virtual/start")
    async def session_virtual_start(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        try:
            return json_from_runtime(S.ACTION_VIRTUAL_START, broker.start_virtual(**body))
        except Exception as exc:
            return json_error(S.ACTION_VIRTUAL_START, exc)

    @app.post("/session/mirror/start")
    async def session_mirror_start(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        try:
            return json_from_runtime(S.ACTION_MIRROR_START, broker.start_mirror(**body))
        except Exception as exc:
            return json_error(S.ACTION_MIRROR_START, exc)

    @app.post("/session/relay/start")
    async def session_relay_start(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        try:
            return json_from_runtime(S.ACTION_RELAY_START, broker.start_relay(**body))
        except Exception as exc:
            return json_error(S.ACTION_RELAY_START, exc)

    @app.post("/session/terminal/open")
    async def session_terminal_open(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        try:
            return json_from_runtime(S.ACTION_TERMINAL_START, broker.start_terminal(**body))
        except Exception as exc:
            return json_error(S.ACTION_TERMINAL_START, exc)

    @app.post("/session/screencast/start")
    async def session_screencast_start(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        try:
            payload = await asyncio.to_thread(
                broker.start_screencast,
                interactive=bool(body.get("interactive", True)),
                timeout_s=float(body.get("timeout_s", 120)),
                multiple=body.get("multiple"),
            )
            return json_from_runtime(S.ACTION_SCREENCAST_START, payload)
        except Exception as exc:
            return json_error(S.ACTION_SCREENCAST_START, exc)

    @app.post("/session/screencast/stop")
    def session_screencast_stop(
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        try:
            return json_from_runtime(S.ACTION_SCREENCAST_STOP, broker.stop_screencast())
        except Exception as exc:
            return json_error(S.ACTION_SCREENCAST_STOP, exc)

    @app.get("/session/screencast/status")
    def session_screencast_status(
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        check_auth(authorization)
        return success(S.ACTION_SCREENCAST_STATUS, strip_ok(broker.screencast_status()))

    @app.post("/session/{session_id}/stop")
    def session_stop(
        session_id: str,
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        try:
            return json_from_runtime(S.ACTION_SESSION_STOP, broker.stop_session(session_id))
        except Exception as exc:
            return json_error(S.ACTION_SESSION_STOP, exc)
