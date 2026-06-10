"""Capture frame routes."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import Depends, FastAPI, Header
from fastapi.responses import JSONResponse

from .. import schemas as S
from ..runtime import AgentRuntime
from ._audit_execute import execute_audited_service
from ..audit_context import AuditContext
from ._audit_headers import read_audit_headers


def register_routes(
    app: FastAPI,
    broker: AgentRuntime,
    check_auth: Callable[[str | None], None],
) -> None:
    @app.post("/capture/frame")
    async def capture_frame(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
        audit: AuditContext = Depends(read_audit_headers),
    ) -> JSONResponse:
        check_auth(authorization)
        return await execute_audited_service(
            S.ACTION_CAPTURE_FRAME,
            body,
            audit=audit,
            fallback=broker.capture_frame,
        )
