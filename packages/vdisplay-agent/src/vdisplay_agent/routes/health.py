"""Health, capabilities, diagnostics, outputs, and windows routes."""

from __future__ import annotations

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
    def health(authorization: str | None = Header(default=None)) -> dict[str, Any]:
        check_auth(authorization)
        return success(
            S.ACTION_HEALTH,
            {"status": "ok", "service": "vdisplay-agent", "broker": "vdisplay-agent"},
        )

    @app.get("/version")
    def version(authorization: str | None = Header(default=None)) -> dict[str, Any]:
        check_auth(authorization)
        return success(
            S.ACTION_VERSION,
            {
                "version": __version__,
                "control_api": _control_api_enabled(app),
            },
        )

    @app.get("/capabilities")
    def capabilities(authorization: str | None = Header(default=None)) -> dict[str, Any]:
        check_auth(authorization)
        return success(S.ACTION_CAPABILITIES, broker.platform_capabilities())

    @app.get("/diagnostics")
    def diagnostics(
        display: str | None = Query(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        check_auth(authorization)
        return success(S.ACTION_DIAGNOSTICS, broker.diagnostics(display=display))

    @app.get("/outputs")
    def outputs(
        display: str | None = Query(default=None),
        include_all: bool = Query(default=True),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        check_auth(authorization)
        return success(
            S.ACTION_OUTPUTS,
            broker.outputs(display=display, include_all=include_all),
        )

    @app.get("/windows")
    def windows(
        request: Request,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        check_auth(authorization)
        params = dict(request.query_params)
        return success(S.ACTION_WINDOWS, broker.list_windows(**params))
