"""Accessibility control-plane routes."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, Header, Query
from fastapi.responses import JSONResponse

from .. import schemas as S
from ..envelope import json_error, json_from_runtime, strip_ok, success
from ..runtime import AgentRuntime


def register_routes(
    app: FastAPI,
    broker: AgentRuntime,
    check_auth: Callable[[str | None], None],
) -> None:
    @app.get("/diagnostics/control")
    def diagnostics_control(
        display: str | None = Query(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        check_auth(authorization)
        return success(S.ACTION_CONTROL_DIAGNOSTICS, strip_ok(broker.diagnose_control(display=display)))

    @app.post("/controls/list")
    async def controls_list(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        try:
            payload = await asyncio.to_thread(broker.list_controls, body)
            return json_from_runtime(S.ACTION_CONTROLS_LIST, payload)
        except Exception as exc:
            return json_error(S.ACTION_CONTROLS_LIST, exc)

    @app.post("/controls/find")
    async def controls_find(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        try:
            payload = await asyncio.to_thread(broker.find_controls, body)
            return json_from_runtime(S.ACTION_CONTROLS_FIND, payload)
        except Exception as exc:
            return json_error(S.ACTION_CONTROLS_FIND, exc)

    @app.post("/control/invoke")
    async def control_invoke(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        try:
            payload = await asyncio.to_thread(broker.invoke_control, body)
            return json_from_runtime(S.ACTION_CONTROL_INVOKE, payload)
        except Exception as exc:
            return json_error(S.ACTION_CONTROL_INVOKE, exc)

    @app.post("/control/focus")
    async def control_focus(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        try:
            payload = await asyncio.to_thread(broker.focus_control, body)
            return json_from_runtime(S.ACTION_CONTROL_FOCUS, payload)
        except Exception as exc:
            return json_error(S.ACTION_CONTROL_FOCUS, exc)

    @app.post("/control/set-value")
    async def control_set_value(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        try:
            payload = await asyncio.to_thread(broker.set_control_value, body)
            return json_from_runtime(S.ACTION_CONTROL_SET_VALUE, payload)
        except Exception as exc:
            return json_error(S.ACTION_CONTROL_SET_VALUE, exc)
