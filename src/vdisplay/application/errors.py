"""Stable error codes for command execution and agent HTTP envelope."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    NOT_SUPPORTED = "not_supported"
    DEPENDENCY_MISSING = "dependency_missing"
    PERMISSION_REQUIRED = "permission_required"
    SESSION_NOT_FOUND = "session_not_found"
    INVALID_REQUEST = "invalid_request"
    BACKEND_UNAVAILABLE = "backend_unavailable"
    INTERNAL = "internal"


@dataclass
class ApplicationError:
    code: ErrorCode
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code.value, "message": self.message, "details": self.details}


def error_from_exception(exc: Exception) -> ApplicationError:
    from ..exceptions import BackendNotAvailableError, CapabilityError, VDisplayError

    if isinstance(exc, CapabilityError):
        return ApplicationError(ErrorCode.NOT_SUPPORTED, str(exc))
    if isinstance(exc, BackendNotAvailableError):
        return ApplicationError(ErrorCode.BACKEND_UNAVAILABLE, str(exc))
    if isinstance(exc, VDisplayError):
        return ApplicationError(ErrorCode.INVALID_REQUEST, str(exc))
    return ApplicationError(ErrorCode.INTERNAL, str(exc))
