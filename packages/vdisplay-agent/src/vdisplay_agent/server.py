"""Local REST API for vdisplay-agent (localhost-only broker)."""

from __future__ import annotations

import os

from fastapi import FastAPI

from .runtime import AgentRuntime
from .routes import register_all_routes


def create_app(runtime: AgentRuntime | None = None):
    os.environ["VDISPLAY_AGENT_BROKER"] = "1"

    app = FastAPI(title="vdisplay-agent", version="0.1.0")
    broker = runtime or AgentRuntime()
    register_all_routes(app, broker)

    @app.on_event("shutdown")
    def _shutdown() -> None:
        broker.shutdown()

    app.state.runtime = broker
    return app
