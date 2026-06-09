"""Sampler loop routes."""

from __future__ import annotations

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
    @app.post("/sampler/start")
    async def sampler_start(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        try:
            return json_from_runtime(S.ACTION_SAMPLER_START, broker.start_sampler(body))
        except Exception as exc:
            return json_error(S.ACTION_SAMPLER_START, exc)

    @app.post("/sampler/stop")
    def sampler_stop(
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        try:
            return json_from_runtime(S.ACTION_SAMPLER_STOP, broker.stop_sampler())
        except Exception as exc:
            return json_error(S.ACTION_SAMPLER_STOP, exc)

    @app.get("/sampler/status")
    def sampler_status(
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        check_auth(authorization)
        return success(S.ACTION_SAMPLER_STATUS, strip_ok(broker.sampler_status()))
