"""Local REST API for vdisplay-agent (localhost-only broker)."""

from __future__ import annotations

import os

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

    app = FastAPI(title="vdisplay-agent", version=__version__)
    broker = runtime or AgentRuntime()
    register_all_routes(app, broker)

    @app.on_event("startup")
    def _startup() -> None:
        broker.recover_tasks()

    @app.on_event("shutdown")
    def _shutdown() -> None:
        try:
            broker.shutdown()
        except Exception as exc:
            import logging

            logging.getLogger(__name__).warning("agent shutdown cleanup failed: %s", exc)

    app.state.runtime = broker
    return app
