"""Thin SDK client for vdisplay-agent (no direct capture/input in client process)."""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from typing import Any

from .agent_config import resolve_agent_token
from .agent_envelope import flatten_agent_envelope
from .application.commands import CommandRequest, CommandResult, CommandVerb
from .application.errors import ApplicationError, ErrorCode, error_from_exception
from .exceptions import VDisplayError


def _route_command(cmd: CommandRequest) -> tuple[str, str, dict[str, Any] | None]:
    """Map CommandRequest to broker HTTP (method, path, body)."""
    verb = cmd.verb
    if verb == CommandVerb.HEALTH:
        return "GET", "/health", None
    if verb == CommandVerb.CAPABILITIES:
        return "GET", "/capabilities", None
    if verb in {CommandVerb.MONITORS, CommandVerb.OUTPUTS}:
        query: list[str] = []
        if cmd.display:
            query.append(f"display={cmd.display}")
        if not cmd.include_all:
            query.append("include_all=false")
        suffix = f"?{'&'.join(query)}" if query else ""
        return "GET", f"/outputs{suffix}", None
    if verb == CommandVerb.WINDOWS:
        params = {
            "display": cmd.display,
            "include_all": str(cmd.include_all).lower(),
            "match_class": cmd.match_class,
            "match_pid": cmd.match_pid,
            "match_app": cmd.match_app,
            "min_width": cmd.min_width or None,
            "min_height": cmd.min_height or None,
        }
        query = [f"{key}={value}" for key, value in params.items() if value is not None]
        suffix = f"?{'&'.join(query)}" if query else ""
        return "GET", f"/windows{suffix}", None
    if verb == CommandVerb.VIRTUAL_START:
        return (
            "POST",
            "/session/virtual/start",
            {"width": cmd.width, "height": cmd.height, "display": cmd.vd_display},
        )
    raise VDisplayError(f"agent request has no direct route for verb: {verb.value}")


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
        raw = self._send(method, path, body=body)
        if not raw.strip():
            return {}
        payload = self._normalize_payload(json.loads(raw))
        self._raise_on_error(payload)
        return payload

    def _send(self, method: str, path: str, *, body: dict[str, Any] | None = None) -> str:
        request = self._build_request(method, path, body=body)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise VDisplayError(
                f"vdisplay-agent {method} {path}: {self._http_error_message(exc)}"
            ) from exc
        except urllib.error.URLError as exc:
            raise VDisplayError(
                f"vdisplay-agent unreachable at {self.base_url}. "
                "Start: vdisplay-agent serve (or vdisplay agent serve)"
            ) from exc

    def _build_request(
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
        return urllib.request.Request(url, data=data, headers=headers, method=method)

    @staticmethod
    def _http_error_message(exc: urllib.error.HTTPError) -> str:
        detail = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(detail)
            return str(payload.get("error") or payload.get("detail") or detail)
        except json.JSONDecodeError:
            return detail or str(exc)

    @staticmethod
    def _raise_on_error(payload: dict[str, Any]) -> None:
        if payload.get("ok") is not False:
            return
        error = payload.get("error")
        if isinstance(error, dict):
            message = error.get("message") or str(error)
        else:
            message = str(error or "agent request failed")
        raise VDisplayError(message)

    @staticmethod
    def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
        return flatten_agent_envelope(payload)

    def request(self, cmd: CommandRequest) -> CommandResult:
        """Execute a CommandRequest via a single broker HTTP call."""
        try:
            method, path, body = _route_command(cmd)
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

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def capabilities(self) -> dict[str, Any]:
        return self._request("GET", "/capabilities")

    def diagnostics(self, *, display: str | None = None) -> dict[str, Any]:
        suffix = f"?display={display}" if display else ""
        return self._request("GET", f"/diagnostics{suffix}")

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

    def start_screencast(
        self,
        *,
        interactive: bool = True,
        timeout_s: float = 120.0,
        multiple: bool | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"interactive": interactive, "timeout_s": timeout_s}
        if multiple is not None:
            body["multiple"] = multiple
        return self._request("POST", "/session/screencast/start", body=body)

    def stop_screencast(self) -> dict[str, Any]:
        return self._request("POST", "/session/screencast/stop")

    def screencast_status(self) -> dict[str, Any]:
        return self._request("GET", "/session/screencast/status")

    def stop_session(self, session_id: str) -> dict[str, Any]:
        return self._request("POST", f"/session/{session_id}/stop")

    def sampler_start(
        self,
        *,
        interval_s: float = 1.0,
        mode: str = "desktop",
        source: str | None = None,
        display: str | None = None,
        vd_display: str = ":99",
        out_dir: str = "./captures",
        max_frames: int | None = None,
        dedupe: bool = True,
        width: int = 1280,
        height: int = 720,
        format: str = "png",
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/sampler/start",
            body={
                "interval_s": interval_s,
                "mode": mode,
                "source": source,
                "display": display,
                "vd_display": vd_display,
                "out_dir": out_dir,
                "max_frames": max_frames,
                "dedupe": dedupe,
                "width": width,
                "height": height,
                "format": format,
            },
        )

    def sampler_stop(self) -> dict[str, Any]:
        return self._request("POST", "/sampler/stop")

    def sampler_status(self) -> dict[str, Any]:
        return self._request("GET", "/sampler/status")

    def diagnose_control(self, *, display: str | None = None) -> dict[str, Any]:
        params = {}
        if display:
            params["display"] = display
        return self._request("GET", "/diagnostics/control", params=params)

    def list_controls(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request("POST", "/controls/list", body=body or {})

    def find_controls(self, body: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/controls/find", body=body)

    def invoke_control(self, body: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/control/invoke", body=body)

    def focus_control(self, body: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/control/focus", body=body)

    def set_control_value(self, body: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/control/set-value", body=body)

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
        region: tuple[int, int, int, int] | list[int] | dict[str, int] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "session_id": session_id,
            "monitor": monitor,
            "source": source,
            "target": target,
            "display": display,
            "prefer_mirror": prefer_mirror,
            "all_monitors": all_monitors,
            "out_dir": out_dir,
            "output": output,
        }
        if region is not None:
            body["region"] = region
        return self._request("POST", "/capture/frame", body=body)

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
