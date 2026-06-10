"""Thin SDK client for vdisplay-agent (no direct capture/input in client process)."""

from __future__ import annotations

from typing import Any

from .application.commands import CommandRequest, CommandResult
from .application.errors import ApplicationError, ErrorCode, error_from_exception
from .client_api import AgentClientApiMixin
from .client_routes import route_command
from .exceptions import VDisplayError

# Backward-compatible alias for tests and callers.
_route_command = route_command


class AgentClient(AgentClientApiMixin):
    """HTTP client for the local vdisplay-agent broker."""

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.request_json(method, path, body=body)

    def request(self, cmd: CommandRequest) -> CommandResult:
        """Execute a CommandRequest via a single broker HTTP call."""
        try:
            method, path, body = route_command(cmd)
            data = self._request(method, path, body=body)
            return CommandResult.success(action=cmd.action, data=data, command=cmd.line)
        except VDisplayError as exc:
            return CommandResult.failure(
                action=cmd.action,
                error=error_from_exception(exc),
                command=cmd.line,
            )
        except Exception as exc:
            return CommandResult.failure(
                action=cmd.action,
                error=ApplicationError(ErrorCode.INTERNAL, str(exc)),
                command=cmd.line,
            )


__all__ = ["AgentClient", "route_command", "_route_command"]
