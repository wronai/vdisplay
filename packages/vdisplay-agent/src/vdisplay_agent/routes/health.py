"""Health, capabilities, diagnostics, outputs, and windows routes."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, Header, Query
from starlette.requests import Request

from .. import __version__, schemas as S
from ..envelope import success
from ..runtime import AgentRuntime


def _control_api_enabled(app: FastAPI) -> bool:
    return any(getattr(route, "path", None) == "/control/invoke" for route in app.routes)


def register_routes(
    app: FastAPI,
    broker: AgentRuntime,
    check_auth: Callable[[str | None], None],
) -> None:
    @app.get("/health")
    async def health(authorization: str | None = Header(default=None)) -> dict[str, Any]:
        check_auth(authorization)
        return success(
            S.ACTION_HEALTH,
            {"status": "ok", "service": "vdisplay-agent", "broker": "vdisplay-agent"},
        )

    @app.get("/version")
    async def version(authorization: str | None = Header(default=None)) -> dict[str, Any]:
        check_auth(authorization)
        return success(
            S.ACTION_VERSION,
            {
                "version": __version__,
                "control_api": _control_api_enabled(app),
            },
        )

    @app.get("/capabilities")
    async def capabilities(authorization: str | None = Header(default=None)) -> dict[str, Any]:
        check_auth(authorization)
        payload = await asyncio.to_thread(broker.platform_capabilities)
        return success(S.ACTION_CAPABILITIES, payload)

    @app.get("/diagnostics")
    async def diagnostics(
        display: str | None = Query(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        check_auth(authorization)
        payload = await asyncio.to_thread(broker.diagnostics, display=display)
        return success(S.ACTION_DIAGNOSTICS, payload)

    @app.get("/outputs")
    async def outputs(
        display: str | None = Query(default=None),
        include_all: bool = Query(default=True),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        check_auth(authorization)
        payload = await asyncio.to_thread(
            broker.outputs,
            display=display,
            include_all=include_all,
        )
        return success(S.ACTION_OUTPUTS, payload)

    @app.get("/windows")
    async def windows(
        request: Request,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        check_auth(authorization)
        params = dict(request.query_params)
        payload = await asyncio.to_thread(broker.list_windows, **params)
        return success(S.ACTION_WINDOWS, payload)
