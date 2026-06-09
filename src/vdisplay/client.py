"""Thin SDK client for vdisplay-agent (no direct capture/input in client process)."""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from typing import Any

from .agent_config import resolve_agent_token
from .exceptions import VDisplayError


class AgentClient:
    """HTTP client for the local vdisplay-agent broker."""

    def __init__(self, base_url: str, *, token: str | None = None, timeout: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token if token is not None else resolve_agent_token()
        self.timeout = timeout

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        data = None
        headers = {"Accept": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(detail)
                message = payload.get("error") or payload.get("detail") or detail
            except json.JSONDecodeError:
                message = detail or str(exc)
            raise VDisplayError(f"vdisplay-agent {method} {path}: {message}") from exc
        except urllib.error.URLError as exc:
            raise VDisplayError(
                f"vdisplay-agent unreachable at {self.base_url}. "
                "Start: vdisplay-agent serve (or vdisplay agent serve)"
            ) from exc

        if not raw.strip():
            return {}
        payload = json.loads(raw)
        payload = self._normalize_payload(payload)
        if isinstance(payload, dict) and payload.get("ok") is False:
            error = payload.get("error")
            if isinstance(error, dict):
                message = error.get("message") or str(error)
            else:
                message = str(error or "agent request failed")
            raise VDisplayError(message)
        return payload

    @staticmethod
    def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            from vdisplay_agent.envelope import flatten_envelope
        except ImportError:
            return payload
        return flatten_envelope(payload)

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def capabilities(self) -> dict[str, Any]:
        return self._request("GET", "/capabilities")

    def diagnostics(self) -> dict[str, Any]:
        return self._request("GET", "/diagnostics")

    def outputs(self, *, display: str | None = None, include_all: bool = True) -> dict[str, Any]:
        query = []
        if display:
            query.append(f"display={display}")
        if not include_all:
            query.append("include_all=false")
        suffix = f"?{'&'.join(query)}" if query else ""
        return self._request("GET", f"/outputs{suffix}")

    def windows(self, **filters: Any) -> dict[str, Any]:
        query = [f"{key}={value}" for key, value in filters.items() if value is not None]
        suffix = f"?{'&'.join(query)}" if query else ""
        return self._request("GET", f"/windows{suffix}")

    def start_virtual(
        self,
        *,
        width: int = 1280,
        height: int = 720,
        display: str = ":99",
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/session/virtual/start",
            body={"width": width, "height": height, "display": display},
        )

    def start_mirror(
        self,
        *,
        source: str = "primary",
        target: str | None = None,
        display: str | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/session/mirror/start",
            body={"source": source, "target": target, "display": display},
        )

    def start_relay(self, *, display: str | None = None) -> dict[str, Any]:
        return self._request("POST", "/session/relay/start", body={"display": display})

    def start_screencast(self, *, interactive: bool = True, timeout_s: float = 120.0) -> dict[str, Any]:
        return self._request(
            "POST",
            "/session/screencast/start",
            body={"interactive": interactive, "timeout_s": timeout_s},
        )

    def stop_screencast(self) -> dict[str, Any]:
        return self._request("POST", "/session/screencast/stop")

    def screencast_status(self) -> dict[str, Any]:
        return self._request("GET", "/session/screencast/status")

    def stop_session(self, session_id: str) -> dict[str, Any]:
        return self._request("POST", f"/session/{session_id}/stop")

    def capture_frame(
        self,
        *,
        session_id: str | None = None,
        monitor: int | None = None,
        source: str | None = None,
        target: str | None = None,
        display: str | None = None,
        prefer_mirror: bool = False,
        all_monitors: bool = False,
        out_dir: str | None = None,
        output: str | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/capture/frame",
            body={
                "session_id": session_id,
                "monitor": monitor,
                "source": source,
                "target": target,
                "display": display,
                "prefer_mirror": prefer_mirror,
                "all_monitors": all_monitors,
                "out_dir": out_dir,
                "output": output,
            },
        )

    def capture_png_bytes(self, **kwargs: Any) -> tuple[bytes, dict[str, Any]]:
        payload = self.capture_frame(**kwargs)
        encoded = payload.get("png_base64")
        if not encoded:
            raise VDisplayError("agent capture response missing png_base64")
        meta = dict(payload)
        meta.pop("png_base64", None)
        return base64.b64decode(encoded), meta

    def adopt_window(self, **kwargs: Any) -> dict[str, Any]:
        return self._request("POST", "/window/adopt", body=kwargs)

    def release_window(self, **kwargs: Any) -> dict[str, Any]:
        return self._request("POST", "/window/release", body=kwargs)
