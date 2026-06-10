"""CLI / env session context for audit recording."""

from __future__ import annotations

import os
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterator

from .commands import CommandRequest

HEADER_SESSION_ID = "X-VDisplay-Session-Id"
HEADER_SESSION_DIR = "X-VDisplay-Session-Dir"
HEADER_REQUEST_ID = "X-VDisplay-Request-Id"
HEADER_REQUEST_SOURCE = "X-VDisplay-Request-Source"

_audit_command: ContextVar[CommandRequest | None] = ContextVar("vdisplay_audit_command", default=None)


@dataclass(frozen=True)
class AuditContext:
    session_id: str | None = None
    session_dir: str | None = None
    request_id: str | None = None
    request_source: str | None = None

    @property
    def should_record(self) -> bool:
        return bool(self.session_dir or self.session_id)


def apply_cli_session_args(args: Any) -> None:
    """Configure session recording env from root CLI flags (call before command handler)."""
    if getattr(args, "session", False):
        os.environ.setdefault("VDISPLAY_SESSION", "1")
    audit_id = getattr(args, "audit_session_id", None)
    if audit_id:
        os.environ["VDISPLAY_SESSION_ID"] = str(audit_id).strip()
        os.environ.setdefault("VDISPLAY_SESSION", "1")


def enrich_command_request(cmd: CommandRequest) -> CommandRequest:
    """Fill audit session fields from env when not set on the request."""
    session_id = cmd.session_id or os.environ.get("VDISPLAY_SESSION_ID", "").strip() or None
    request_id = cmd.request_id or str(uuid.uuid4())
    updates: dict[str, Any] = {"request_id": request_id}
    if session_id:
        updates["session_id"] = session_id
    if not cmd.request_source:
        updates["request_source"] = "cli"
    return replace(cmd, **updates)


def agent_audit_delegated() -> bool:
    """When true, agent-routed commands record on the broker instead of the client."""
    return os.environ.get("VDISPLAY_AGENT_AUDIT_DELEGATE", "1").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def ensure_audit_session_dir(cmd: CommandRequest) -> Path | None:
    """Resolve and pin the audit session directory before agent HTTP calls."""
    from .session_recorder import resolve_session_root, session_recording_enabled

    if not session_recording_enabled():
        return None
    root = resolve_session_root(cmd)
    if root is None:
        return None
    resolved = root.expanduser()
    if not resolved.is_absolute():
        resolved = Path.cwd() / resolved
    resolved = resolved.resolve()
    resolved.mkdir(parents=True, exist_ok=True)
    os.environ["VDISPLAY_SESSION_DIR"] = str(resolved)
    os.environ.setdefault("VDISPLAY_SESSION", "1")
    return resolved


def audit_headers_for_command(cmd: CommandRequest) -> dict[str, str]:
    """HTTP headers propagated to vdisplay-agent for broker-side audit recording."""
    headers: dict[str, str] = {}
    if cmd.session_id:
        headers[HEADER_SESSION_ID] = cmd.session_id
    if cmd.request_id:
        headers[HEADER_REQUEST_ID] = cmd.request_id
    if cmd.request_source:
        headers[HEADER_REQUEST_SOURCE] = cmd.request_source
    session_dir = os.environ.get("VDISPLAY_SESSION_DIR", "").strip()
    if session_dir:
        headers[HEADER_SESSION_DIR] = str(Path(session_dir).expanduser().resolve())
    return headers


def current_audit_headers() -> dict[str, str]:
    cmd = _audit_command.get()
    if cmd is None:
        return {}
    return audit_headers_for_command(cmd)


@contextmanager
def bind_audit_command(cmd: CommandRequest) -> Iterator[CommandRequest]:
    token = _audit_command.set(cmd)
    try:
        yield cmd
    finally:
        _audit_command.reset(token)


def audit_context_from_mapping(headers: dict[str, str | None]) -> AuditContext:
    """Build audit context from HTTP header mapping (case-insensitive keys ok)."""
    normalized = {str(key).lower(): value for key, value in headers.items() if value}
    return AuditContext(
        session_id=normalized.get(HEADER_SESSION_ID.lower()),
        session_dir=normalized.get(HEADER_SESSION_DIR.lower()),
        request_id=normalized.get(HEADER_REQUEST_ID.lower()),
        request_source=normalized.get(HEADER_REQUEST_SOURCE.lower()),
    )
