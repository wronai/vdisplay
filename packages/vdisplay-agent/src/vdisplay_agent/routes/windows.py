"""Window adopt/release routes."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse

from .. import schemas as S
from ..envelope import json_error, json_from_runtime
from ..runtime import AgentRuntime


def register_routes(
    app: FastAPI,
    broker: AgentRuntime,
    check_auth: Callable[[str | None], None],
) -> None:
    @app.post("/window/adopt")
    async def window_adopt(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        try:
            return json_from_runtime(S.ACTION_WINDOW_ADOPT, broker.adopt_window(body))
        except Exception as exc:
            return json_error(S.ACTION_WINDOW_ADOPT, exc)

    @app.post("/window/release")
    async def window_release(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        try:
            return json_from_runtime(S.ACTION_WINDOW_RELEASE, broker.release_window(body))
        except Exception as exc:
            return json_error(S.ACTION_WINDOW_RELEASE, exc)
