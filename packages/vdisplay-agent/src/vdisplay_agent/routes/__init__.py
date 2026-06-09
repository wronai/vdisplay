"""Register all vdisplay-agent HTTP route groups."""

from __future__ import annotations

from fastapi import FastAPI

from ..runtime import AgentRuntime
from . import capture, control, health, sampler, session, windows
from .auth import expected_token, make_check_auth


def register_all_routes(app: FastAPI, broker: AgentRuntime) -> None:
    check_auth = make_check_auth(expected_token())
    for module in (health, session, sampler, capture, windows, control):
        module.register_routes(app, broker, check_auth)
