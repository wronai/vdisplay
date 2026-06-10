"""CLI / env session context for audit recording."""

from __future__ import annotations

import os
import uuid
from dataclasses import replace
from typing import Any

from .commands import CommandRequest


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
