"""Capture frame routes."""

from __future__ import annotations

import asyncio
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
    @app.post("/capture/frame")
    async def capture_frame(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        try:
            payload = await asyncio.to_thread(broker.capture_frame, body)
            return json_from_runtime(S.ACTION_CAPTURE_FRAME, payload)
        except Exception as exc:
            return json_error(S.ACTION_CAPTURE_FRAME, exc)
