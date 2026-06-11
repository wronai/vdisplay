"""Single place for agent vs local execution routing."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Literal
from urllib.parse import urlparse

from ..agent_config import resolve_agent_url, use_agent, _default_agent_base

from .commands import CommandRequest, CommandVerb

if TYPE_CHECKING:
    from ..client import AgentClient

Route = Literal["agent", "local"]

# Same-host discovery is identical in-process; skip IPC so a hung capture cannot block monitors.
_LOCAL_DISCOVERY_VERBS = frozenset(
    {
        CommandVerb.MONITORS,
        CommandVerb.OUTPUTS,
        CommandVerb.WINDOWS,
        CommandVerb.ALL,
    }
)


def _is_local_agent_url(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host in {"127.0.0.1", "localhost", "::1"}


def agent_client_optional(*, allow_auto: bool = True) -> AgentClient | None:
    url = resolve_agent_url(allow_auto=allow_auto)
    if not url:
        return None
    from ..client import AgentClient

    return AgentClient(url)


def agent_client_required(*, allow_auto: bool = True) -> AgentClient:
    client = agent_client_optional(allow_auto=allow_auto)
    if client is None:
        from ..exceptions import VDisplayError

        raise VDisplayError(
            "VDISPLAY_AGENT_URL is not set and no local agent responded on "
            f"{_default_agent_base()} (try: vdisplay-agent serve)"
        )
    return client


def prefer_agent() -> bool:
    """Deprecated — use ExecutionPolicy.route() instead."""
    return use_agent()


def resolve_apps_only(
    *,
    include_all: bool,
    apps_only: bool | None,
    include_internal: bool | None,
) -> bool:
    if apps_only is not None:
        return apps_only
    if include_internal is not None:
        return not include_internal
    return not include_all


class ExecutionPolicy:
    """Decide whether a command runs via vdisplay-agent or in-process."""

    def route(self, cmd: CommandRequest) -> Route:
        if cmd.local_only:
            return "local"
        if os.environ.get("VDISPLAY_AGENT_BROKER", "").strip().lower() in {"1", "true", "yes"}:
            return "local"
        if cmd.verb == CommandVerb.SCREENSHOT and cmd.mode == "virtual":
            return "local"
        url = resolve_agent_url(allow_auto=True)
        if url and cmd.verb in _LOCAL_DISCOVERY_VERBS:
            force_remote = os.environ.get("VDISPLAY_AGENT_FORCE_REMOTE", "").strip().lower() in {
                "1",
                "true",
                "yes",
            }
            if _is_local_agent_url(url) and not force_remote:
                return "local"
        if url is not None:
            return "agent"
        return "local"

    def meta_for(self, route: Route) -> dict[str, str]:
        from ..control.descriptors import detect_platform_profile

        platform = detect_platform_profile()
        return {
            "route": route,
            "agent_url": resolve_agent_url(allow_auto=True) or "",
            "host_environment": platform.host_environment.value,
        }


_default_policy = ExecutionPolicy()


def get_execution_policy() -> ExecutionPolicy:
    return _default_policy
