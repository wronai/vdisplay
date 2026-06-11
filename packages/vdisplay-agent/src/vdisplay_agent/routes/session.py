"""Virtual, mirror, relay, and screencast session routes."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from fastapi import Depends, FastAPI, Header
from fastapi.responses import JSONResponse
from vdisplay.application.commands import CommandVerb

from .. import schemas as S
from ..envelope import json_error, json_from_runtime, strip_ok, success
from ..runtime import AgentRuntime
from ._audit_execute import execute_audit_route, execute_audited_service
from ..audit_context import AuditContext
from ._audit_headers import read_audit_headers


def register_routes(
    app: FastAPI,
    broker: AgentRuntime,
    check_auth: Callable[[str | None], None],
) -> None:
    @app.post("/session/virtual/start")
    async def session_virtual_start(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
        audit: AuditContext = Depends(read_audit_headers),
    ) -> JSONResponse:
        check_auth(authorization)
        return await execute_audited_service(
            S.ACTION_VIRTUAL_START,
            body,
            audit=audit,
            fallback=lambda payload: broker.start_virtual(**payload),
            record_verb=CommandVerb.VIRTUAL_START,
        )

    @app.post("/session/mirror/start")
    async def session_mirror_start(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
        audit: AuditContext = Depends(read_audit_headers),
    ) -> JSONResponse:
        check_auth(authorization)
        return await execute_audited_service(
            S.ACTION_MIRROR_START,
            body,
            audit=audit,
            fallback=lambda payload: broker.start_mirror(**payload),
            record_verb=CommandVerb.MIRROR,
        )

    @app.post("/session/relay/start")
    async def session_relay_start(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
        audit: AuditContext = Depends(read_audit_headers),
    ) -> JSONResponse:
        check_auth(authorization)
        from ._audit_execute import execute_audited_service

        return await execute_audited_service(
            S.ACTION_RELAY_START,
            body,
            audit=audit,
            fallback=lambda payload: broker.start_relay(**payload),
            record_verb=CommandVerb.ADOPT,
        )

    @app.post("/session/browser/open")
    async def session_browser_open(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
        audit: AuditContext = Depends(read_audit_headers),
    ) -> JSONResponse:
        check_auth(authorization)

        def _start_browser(payload: dict[str, Any]) -> dict[str, Any]:
            mapped = dict(payload)
            if mapped.get("app") and not mapped.get("url"):
                mapped["url"] = mapped["app"]
            return broker.start_browser(**mapped)

        return await execute_audit_route(
            S.ACTION_BROWSER_START,
            CommandVerb.BROWSER_OPEN,
            body,
            audit=audit,
            fallback=_start_browser,
        )

    @app.post("/session/terminal/open")
    async def session_terminal_open(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
        audit: AuditContext = Depends(read_audit_headers),
    ) -> JSONResponse:
        check_auth(authorization)
        return await execute_audit_route(
            S.ACTION_TERMINAL_START,
            CommandVerb.TERMINAL_OPEN,
            body,
            audit=audit,
            fallback=lambda payload: broker.start_terminal(**payload),
        )

    @app.post("/session/screencast/start")
    async def session_screencast_start(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
        audit: AuditContext = Depends(read_audit_headers),
    ) -> JSONResponse:
        check_auth(authorization)
        from ._audit_execute import execute_audited_service

        return await execute_audited_service(
            S.ACTION_SCREENCAST_START,
            body,
            audit=audit,
            fallback=lambda payload: broker.start_screencast(
                interactive=bool(payload.get("interactive", True)),
                timeout_s=float(payload.get("timeout_s", 120)),
                multiple=payload.get("multiple"),
            ),
            record_verb=CommandVerb.SCREENCAST_START,
        )

    @app.post("/session/screencast/adopt")
    def session_screencast_adopt(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        try:
            return json_from_runtime(S.ACTION_SCREENCAST_ADOPT, broker.adopt_screencast(body))
        except Exception as exc:
            return json_error(S.ACTION_SCREENCAST_ADOPT, exc)

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

    @app.get("/sessions")
    def sessions_list(
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        check_auth(authorization)
        return success(S.ACTION_SESSIONS_LIST, strip_ok(broker.list_sessions()))

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
