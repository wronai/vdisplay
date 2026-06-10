"""Apply propagated audit session metadata on the broker host."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from vdisplay.application.session_context import AuditContext, audit_context_from_mapping


def audit_context_from_headers(
    *,
    session_id: str | None = None,
    session_dir: str | None = None,
    request_id: str | None = None,
    request_source: str | None = None,
) -> AuditContext:
    return AuditContext(
        session_id=session_id,
        session_dir=session_dir,
        request_id=request_id,
        request_source=request_source,
    )


def audit_context_from_fastapi_headers(headers: dict[str, str | None]) -> AuditContext:
    return audit_context_from_mapping(headers)


@contextmanager
def apply_audit_env(ctx: AuditContext) -> Iterator[AuditContext]:
    """Temporarily configure broker env for session_recorder during a request."""
    if not ctx.should_record:
        yield ctx
        return

    saved: dict[str, str | None] = {}
    updates: dict[str, str] = {"VDISPLAY_SESSION": "1"}
    if ctx.session_dir:
        path = os.path.expanduser(ctx.session_dir)
        updates["VDISPLAY_SESSION_DIR"] = str(path)
    if ctx.session_id:
        updates["VDISPLAY_SESSION_ID"] = ctx.session_id

    for key, value in updates.items():
        saved[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        yield ctx
    finally:
        for key, previous in saved.items():
            if previous is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = previous
