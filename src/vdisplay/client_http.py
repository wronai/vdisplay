"""HTTP transport helpers for the vdisplay-agent broker."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from .agent_config import resolve_agent_token
from .agent_envelope import flatten_agent_envelope
from .application.session_context import current_audit_headers
from .exceptions import VDisplayError


class AgentHttpTransport:
    """Low-level JSON HTTP client for vdisplay-agent."""

    def __init__(self, base_url: str, *, token: str | None = None, timeout: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token if token is not None else resolve_agent_token()
        self.timeout = timeout

    def request_json(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raw = self.send(method, path, body=body)
        if not raw.strip():
            return {}
        payload = self.normalize_payload(json.loads(raw))
        self.raise_on_error(payload)
        return payload

    def send(self, method: str, path: str, *, body: dict[str, Any] | None = None) -> str:
        request = self.build_request(method, path, body=body)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise VDisplayError(
                f"vdisplay-agent {method} {path}: {self.http_error_message(exc)}"
            ) from exc
        except urllib.error.URLError as exc:
            raise VDisplayError(
                f"vdisplay-agent unreachable at {self.base_url}. "
                "Start: vdisplay-agent serve (or vdisplay agent serve)"
            ) from exc

    def build_request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None,
    ) -> urllib.request.Request:
        url = f"{self.base_url}{path}"
        data = None
        headers = {"Accept": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        headers.update(current_audit_headers())
        return urllib.request.Request(url, data=data, headers=headers, method=method)

    @staticmethod
    def http_error_message(exc: urllib.error.HTTPError) -> str:
        detail = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(detail)
            return str(payload.get("error") or payload.get("detail") or detail)
        except json.JSONDecodeError:
            return detail or str(exc)

    @staticmethod
    def raise_on_error(payload: dict[str, Any]) -> None:
        if payload.get("ok") is not False:
            return
        error = payload.get("error")
        if isinstance(error, dict):
            message = error.get("message") or str(error)
        else:
            message = str(error or "agent request failed")
        raise VDisplayError(message)

    @staticmethod
    def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
        return flatten_agent_envelope(payload)


__all__ = ["AgentHttpTransport"]
