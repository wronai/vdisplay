"""Bearer token auth for agent routes."""

from __future__ import annotations

import os
from collections.abc import Callable

from fastapi import HTTPException


def expected_token() -> str:
    return (os.environ.get("VDISPLAY_AGENT_TOKEN") or "").strip()


def make_check_auth(token: str) -> Callable[[str | None], None]:
    def check_auth(authorization: str | None) -> None:
        if not token:
            return
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="missing bearer token")
        if authorization.removeprefix("Bearer ").strip() != token:
            raise HTTPException(status_code=403, detail="invalid bearer token")

    return check_auth
