from __future__ import annotations

import json
import os

from dsl2vdisplay import dispatch
from dsl2vdisplay.schema_registry import all_schemas, schema_for_verb
from fastapi import FastAPI
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.requests import Request
from starlette.responses import Response


def create_app(*, agent_url: str | None = None):
    """
    REST adapter for vdisplay.

    When VDISPLAY_AGENT_URL is set (or --agent-url), DSL commands route through
    vdisplay-agent — this process does not perform capture/input directly.
    """
    if agent_url:
        os.environ.setdefault("VDISPLAY_AGENT_URL", agent_url.rstrip("/"))

    app = FastAPI(
        title="rest2vdisplay",
        version="0.1.0",
        description="HTTP adapter → dsl2vdisplay → vdisplay-agent (when configured)",
    )

    @app.get("/health")
    def health() -> dict[str, object]:
        from vdisplay.agent_config import resolve_agent_url

        payload: dict[str, object] = {"status": "ok", "service": "rest2vdisplay"}
        url = resolve_agent_url()
        if url:
            from vdisplay.client import AgentClient

            payload["broker"] = url
            payload["agent"] = AgentClient(url).health()
        return payload

    @app.get("/capabilities")
    def capabilities() -> JSONResponse:
        from vdisplay.agent_config import resolve_agent_url

        url = resolve_agent_url()
        if not url:
            return JSONResponse(
                {
                    "ok": False,
                    "error": "Set VDISPLAY_AGENT_URL to query agent capabilities",
                },
                status_code=503,
            )
        from vdisplay.client import AgentClient

        return JSONResponse(AgentClient(url).capabilities())

    @app.get("/v1/schema/{verb}")
    def get_schema(verb: str) -> JSONResponse:
        schema = schema_for_verb(verb)
        if schema is None:
            return JSONResponse({"error": f"unknown verb: {verb}"}, status_code=404)
        return JSONResponse(schema)

    @app.get("/v1/schema")
    def list_schemas() -> JSONResponse:
        return JSONResponse(all_schemas())

    @app.post("/v1/dsl")
    async def post_dsl(request: Request) -> Response:
        ct = request.headers.get("content-type", "text/plain").split(";")[0].strip()
        body = await request.body()
        if ct == "application/json":
            result = dispatch(json.loads(body.decode("utf-8")))
        else:
            result = dispatch(body.decode("utf-8").strip())
        if ct == "text/plain":
            return PlainTextResponse(result.output or json.dumps(result.to_dict(), ensure_ascii=False))
        return JSONResponse(result.to_dict())

    @app.post("/v1/commands")
    async def post_commands(request: Request) -> Response:
        return await post_dsl(request)

    return app
