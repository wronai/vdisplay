"""Accessibility control-plane routes."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, Header, Query
from fastapi.responses import JSONResponse
from vdisplay.application.commands import CommandVerb
from vdisplay.application.session_context import (
    HEADER_REQUEST_ID,
    HEADER_REQUEST_SOURCE,
    HEADER_SESSION_DIR,
    HEADER_SESSION_ID,
)

from .. import schemas as S
from ..audit_context import audit_context_from_headers
from ..envelope import json_error, json_from_runtime, strip_ok, success
from ..runtime import AgentRuntime
from ._audit_execute import execute_control_route


def register_routes(
    app: FastAPI,
    broker: AgentRuntime,
    check_auth: Callable[[str | None], None],
) -> None:
    @app.get("/control/plugins")
    def control_plugins(
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        check_auth(authorization)
        return success(S.ACTION_CONTROL_PLUGINS, strip_ok(broker.list_control_plugins()))

    @app.get("/diagnostics/control")
    def diagnostics_control(
        display: str | None = Query(default=None),
        backend: str = Query(default="auto"),
        environment: str | None = Query(default=None),
        session_id: str | None = Query(default=None),
        role: str | None = Query(default=None),
        name: str | None = Query(default=None),
        app: str | None = Query(default=None),
        dom_css: str | None = Query(default=None),
        dom_xpath: str | None = Query(default=None),
        terminal_line: int | None = Query(default=None),
        terminal_col: int | None = Query(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        check_auth(authorization)
        return success(
            S.ACTION_CONTROL_DIAGNOSTICS,
            strip_ok(
                broker.diagnose_control(
                    display=display,
                    backend=backend,
                    environment=environment,
                    session_id=session_id,
                    role=role,
                    name=name,
                    app=app,
                    dom_css=dom_css,
                    dom_xpath=dom_xpath,
                    terminal_line=terminal_line,
                    terminal_col=terminal_col,
                )
            ),
        )

    @app.post("/controls/list")
    async def controls_list(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
        audit_session_id: str | None = Header(default=None, alias=HEADER_SESSION_ID),
        audit_session_dir: str | None = Header(default=None, alias=HEADER_SESSION_DIR),
        audit_request_id: str | None = Header(default=None, alias=HEADER_REQUEST_ID),
        audit_request_source: str | None = Header(default=None, alias=HEADER_REQUEST_SOURCE),
    ) -> JSONResponse:
        check_auth(authorization)
        audit = audit_context_from_headers(
            session_id=audit_session_id,
            session_dir=audit_session_dir,
            request_id=audit_request_id,
            request_source=audit_request_source,
        )
        return await execute_control_route(
            S.ACTION_CONTROLS_LIST,
            CommandVerb.CONTROLS_LIST,
            body,
            audit=audit,
            fallback=broker.list_controls,
        )

    @app.post("/controls/find")
    async def controls_find(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
        audit_session_id: str | None = Header(default=None, alias=HEADER_SESSION_ID),
        audit_session_dir: str | None = Header(default=None, alias=HEADER_SESSION_DIR),
        audit_request_id: str | None = Header(default=None, alias=HEADER_REQUEST_ID),
        audit_request_source: str | None = Header(default=None, alias=HEADER_REQUEST_SOURCE),
    ) -> JSONResponse:
        check_auth(authorization)
        audit = audit_context_from_headers(
            session_id=audit_session_id,
            session_dir=audit_session_dir,
            request_id=audit_request_id,
            request_source=audit_request_source,
        )
        return await execute_control_route(
            S.ACTION_CONTROLS_FIND,
            CommandVerb.CONTROLS_FIND,
            body,
            audit=audit,
            fallback=broker.find_controls,
        )

    @app.post("/control/invoke")
    async def control_invoke(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
        audit_session_id: str | None = Header(default=None, alias=HEADER_SESSION_ID),
        audit_session_dir: str | None = Header(default=None, alias=HEADER_SESSION_DIR),
        audit_request_id: str | None = Header(default=None, alias=HEADER_REQUEST_ID),
        audit_request_source: str | None = Header(default=None, alias=HEADER_REQUEST_SOURCE),
    ) -> JSONResponse:
        check_auth(authorization)
        audit = audit_context_from_headers(
            session_id=audit_session_id,
            session_dir=audit_session_dir,
            request_id=audit_request_id,
            request_source=audit_request_source,
        )
        return await execute_control_route(
            S.ACTION_CONTROL_INVOKE,
            CommandVerb.CONTROL_CLICK,
            body,
            audit=audit,
            fallback=broker.invoke_control,
        )

    @app.post("/control/focus")
    async def control_focus(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
        audit_session_id: str | None = Header(default=None, alias=HEADER_SESSION_ID),
        audit_session_dir: str | None = Header(default=None, alias=HEADER_SESSION_DIR),
        audit_request_id: str | None = Header(default=None, alias=HEADER_REQUEST_ID),
        audit_request_source: str | None = Header(default=None, alias=HEADER_REQUEST_SOURCE),
    ) -> JSONResponse:
        check_auth(authorization)
        audit = audit_context_from_headers(
            session_id=audit_session_id,
            session_dir=audit_session_dir,
            request_id=audit_request_id,
            request_source=audit_request_source,
        )
        return await execute_control_route(
            S.ACTION_CONTROL_FOCUS,
            CommandVerb.CONTROL_FOCUS,
            body,
            audit=audit,
            fallback=broker.focus_control,
        )

    @app.post("/control/set-value")
    async def control_set_value(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
        audit_session_id: str | None = Header(default=None, alias=HEADER_SESSION_ID),
        audit_session_dir: str | None = Header(default=None, alias=HEADER_SESSION_DIR),
        audit_request_id: str | None = Header(default=None, alias=HEADER_REQUEST_ID),
        audit_request_source: str | None = Header(default=None, alias=HEADER_REQUEST_SOURCE),
    ) -> JSONResponse:
        check_auth(authorization)
        audit = audit_context_from_headers(
            session_id=audit_session_id,
            session_dir=audit_session_dir,
            request_id=audit_request_id,
            request_source=audit_request_source,
        )
        return await execute_control_route(
            S.ACTION_CONTROL_SET_VALUE,
            CommandVerb.CONTROL_SET_VALUE,
            body,
            audit=audit,
            fallback=broker.set_control_value,
        )
