from __future__ import annotations

import json

from dsl2vdisplay import dispatch
from dsl2vdisplay.schema_registry import all_schemas, schema_for_verb


def create_app():
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse, PlainTextResponse, Response

    app = FastAPI(title="rest2vdisplay", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "rest2vdisplay"}

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
