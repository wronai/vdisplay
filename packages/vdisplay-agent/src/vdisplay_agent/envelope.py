"""Stable JSON envelope for vdisplay-agent HTTP responses."""

from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse
from vdisplay.application.errors import ApplicationError, ErrorCode, error_from_exception
from vdisplay.exceptions import VDisplayError


def agent_meta() -> dict[str, str]:
    return {"service": "vdisplay-agent", "broker": "vdisplay-agent"}


def success(action: str, data: dict[str, Any], *, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "ok": True,
        "action": action,
        "data": data,
        "meta": {**agent_meta(), **(meta or {})},
    }


def failure(
    action: str,
    error: ApplicationError,
    *,
    data: dict[str, Any] | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "action": action,
        "data": data or {},
        "error": error.to_dict(),
        "meta": {**agent_meta(), **(meta or {})},
    }


def from_runtime(action: str, payload: dict[str, Any], *, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """Wrap runtime dict (may include legacy top-level ok) into envelope."""
    data = dict(payload)
    ok = bool(data.pop("ok", True))
    if not ok:
        message = str(data.pop("error", None) or "request failed")
        return failure(action, ApplicationError(ErrorCode.INVALID_REQUEST, message), data=data, meta=meta)
    return success(action, data, meta=meta)


def json_success(action: str, data: dict[str, Any], *, status_code: int = 200) -> JSONResponse:
    return JSONResponse(from_runtime(action, {**data, "ok": True}), status_code=status_code)


def json_from_runtime(action: str, payload: dict[str, Any], *, status_code: int = 200) -> JSONResponse:
    return JSONResponse(from_runtime(action, payload), status_code=status_code)


def json_error(action: str, exc: Exception) -> JSONResponse:
    if isinstance(exc, VDisplayError):
        code = ErrorCode.SESSION_NOT_FOUND if "unknown session" in str(exc).lower() else ErrorCode.INVALID_REQUEST
        error = ApplicationError(code, str(exc))
        status = 404 if code == ErrorCode.SESSION_NOT_FOUND else 400
    else:
        error = error_from_exception(exc)
        status = 500 if error.code == ErrorCode.INTERNAL else 400
    try:
        from .broker_events import log_broker_event

        log_broker_event(
            action,
            ok=False,
            error=str(error.message),
            code=error.code.value if hasattr(error.code, "value") else str(error.code),
            status=status,
        )
    except Exception:
        pass
    return JSONResponse(failure(action, error), status_code=status)


def strip_ok(payload: dict[str, Any]) -> dict[str, Any]:
    data = dict(payload)
    data.pop("ok", None)
    return data


def flatten_envelope(payload: dict[str, Any]) -> dict[str, Any]:
    """SDK backward compatibility — merge envelope.data to top level."""
    if "data" in payload and "action" in payload:
        flat = dict(payload.get("data") or {})
        if "ok" in payload:
            flat["ok"] = payload["ok"]
        if payload.get("error"):
            flat["error"] = payload["error"]
        return flat
    return payload
