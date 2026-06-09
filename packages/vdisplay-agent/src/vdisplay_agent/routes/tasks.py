"""Durable broker task routes (PR-11)."""

from __future__ import annotations

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
    @app.get("/tasks")
    def tasks_list(
        status: str | None = Query(default=None),
        kind: str | None = Query(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        check_auth(authorization)
        return success(
            S.ACTION_TASKS_LIST,
            strip_ok(broker.list_tasks(status=status, kind=kind)),
        )

    @app.get("/tasks/{task_id}")
    def tasks_get(
        task_id: str,
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        try:
            return json_from_runtime(S.ACTION_TASK_GET, broker.get_task(task_id))
        except Exception as exc:
            return json_error(S.ACTION_TASK_GET, exc)

    @app.post("/tasks/{task_id}/heartbeat")
    def tasks_heartbeat(
        task_id: str,
        body: dict[str, Any] | None = None,
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        try:
            state = (body or {}).get("state")
            return json_from_runtime(
                S.ACTION_TASK_HEARTBEAT,
                broker.heartbeat_task(task_id, state=state),
            )
        except Exception as exc:
            return json_error(S.ACTION_TASK_HEARTBEAT, exc)

    @app.post("/tasks/{task_id}/stop")
    def tasks_stop(
        task_id: str,
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        try:
            return json_from_runtime(S.ACTION_TASK_STOP, broker.stop_task(task_id))
        except Exception as exc:
            return json_error(S.ACTION_TASK_STOP, exc)
