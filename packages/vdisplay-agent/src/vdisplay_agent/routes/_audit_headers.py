"""FastAPI audit header helpers for broker routes."""

from __future__ import annotations

from fastapi import Header
from vdisplay.application.session_context import (
    HEADER_REQUEST_ID,
    HEADER_REQUEST_SOURCE,
    HEADER_SESSION_DIR,
    HEADER_SESSION_ID,
)

from ..audit_context import AuditContext, audit_context_from_headers


def read_audit_headers(
    audit_session_id: str | None = Header(default=None, alias=HEADER_SESSION_ID),
    audit_session_dir: str | None = Header(default=None, alias=HEADER_SESSION_DIR),
    audit_request_id: str | None = Header(default=None, alias=HEADER_REQUEST_ID),
    audit_request_source: str | None = Header(default=None, alias=HEADER_REQUEST_SOURCE),
) -> AuditContext:
    return audit_context_from_headers(
        session_id=audit_session_id,
        session_dir=audit_session_dir,
        request_id=audit_request_id,
        request_source=audit_request_source,
    )
