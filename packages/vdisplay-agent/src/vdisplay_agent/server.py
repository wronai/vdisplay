"""Local REST API for vdisplay-agent (localhost-only broker)."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import __version__
from .runtime import AgentRuntime
from .routes import register_all_routes


def create_app(runtime: AgentRuntime | None = None):
    os.environ["VDISPLAY_AGENT_BROKER"] = "1"
    try:
        from vdisplay.capture.portal_screencast import ensure_portal_session_env, portal_session_env_status

        ensure_portal_session_env()
        ok, hint = portal_session_env_status()
        if not ok:
            import sys

            print(f"vdisplay-agent: WARN — {hint}", file=sys.stderr)
    except Exception:
        pass

    broker = runtime or AgentRuntime()

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        broker.recover_tasks()
        try:
            yield
        finally:
            try:
                broker.shutdown()
            except Exception as exc:
                import logging

                logging.getLogger(__name__).warning("agent shutdown cleanup failed: %s", exc)

    app = FastAPI(title="vdisplay-agent", version=__version__, lifespan=lifespan)
    register_all_routes(app, broker)

    app.state.runtime = broker
    return app
