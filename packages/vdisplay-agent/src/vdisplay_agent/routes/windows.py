"""Window adopt/release routes."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import Depends, FastAPI, Header
from fastapi.responses import JSONResponse
from vdisplay.application.commands import CommandVerb

from .. import schemas as S
from ..audit_context import AuditContext
from ..runtime import AgentRuntime
from ._audit_execute import execute_audit_route
from ._audit_headers import read_audit_headers


def register_routes(
    app: FastAPI,
    broker: AgentRuntime,
    check_auth: Callable[[str | None], None],
) -> None:
    @app.post("/window/adopt")
    async def window_adopt(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
        audit: AuditContext = Depends(read_audit_headers),
    ) -> JSONResponse:
        check_auth(authorization)
        return await execute_audit_route(
            S.ACTION_WINDOW_ADOPT,
            CommandVerb.ADOPT,
            body,
            audit=audit,
            fallback=broker.adopt_window,
        )

    @app.post("/window/release")
    async def window_release(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
        audit: AuditContext = Depends(read_audit_headers),
    ) -> JSONResponse:
        check_auth(authorization)
        return await execute_audit_route(
            S.ACTION_WINDOW_RELEASE,
            CommandVerb.RELEASE,
            body,
            audit=audit,
            fallback=broker.release_window,
        )
