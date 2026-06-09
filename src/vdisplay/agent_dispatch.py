"""Deprecated — route DSL verbs through application.executor."""

from __future__ import annotations

import warnings
from typing import Any

from .agent_config import resolve_agent_url
from .application.commands import CommandRequest
from .application.executor import execute
from .client import AgentClient
from .exceptions import VDisplayError


def agent_client(url: str | None = None) -> AgentClient:
    resolved = resolve_agent_url(url)
    if not resolved:
        raise VDisplayError("VDISPLAY_AGENT_URL is not set")
    return AgentClient(resolved)


def dispatch_via_agent(cmd: dict[str, Any], *, line: str) -> Any:
    """Execute parsed DSL command through vdisplay-agent (via executor)."""
    warnings.warn(
        "agent_dispatch.dispatch_via_agent is deprecated; use application.executor.execute",
        DeprecationWarning,
        stacklevel=2,
    )
    request = CommandRequest.from_dsl(cmd, line=line)
    return execute(request, force_route="agent").to_dsl_result()
