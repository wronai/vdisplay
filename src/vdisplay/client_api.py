"""High-level broker endpoint helpers for AgentClient."""

from __future__ import annotations

import base64
from typing import Any

from .client_http import AgentHttpTransport
from .exceptions import VDisplayError


class AgentClientApiMixin(AgentHttpTransport):
    """Convenience methods mapping to broker REST endpoints."""

    def health(self) -> dict[str, Any]:
        return self.request_json("GET", "/health")

    def capabilities(self) -> dict[str, Any]:
        return self.request_json("GET", "/capabilities")

    def diagnostics(self, *, display: str | None = None) -> dict[str, Any]:
        suffix = f"?display={display}" if display else ""
        return self.request_json("GET", f"/diagnostics{suffix}")

    def outputs(self, *, display: str | None = None, include_all: bool = True) -> dict[str, Any]:
        query = []
        if display:
            query.append(f"display={display}")
        if not include_all:
            query.append("include_all=false")
        suffix = f"?{'&'.join(query)}" if query else ""
        return self.request_json("GET", f"/outputs{suffix}")

    def windows(self, **filters: Any) -> dict[str, Any]:
        query = [f"{key}={value}" for key, value in filters.items() if value is not None]
        suffix = f"?{'&'.join(query)}" if query else ""
        return self.request_json("GET", f"/windows{suffix}")

    def start_virtual(
        self,
        *,
        width: int = 1280,
        height: int = 720,
        display: str = ":99",
    ) -> dict[str, Any]:
        return self.request_json(
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
        return self.request_json(
            "POST",
            "/session/mirror/start",
            body={"source": source, "target": target, "display": display},
        )

    def start_relay(self, *, display: str | None = None) -> dict[str, Any]:
        return self.request_json("POST", "/session/relay/start", body={"display": display})

    def browser_open(
        self,
        *,
        url: str,
        session_id: str | None = None,
        headless: bool = True,
        title: str | None = None,
        engine: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"url": url, "headless": headless}
        if session_id:
            body["session_id"] = session_id
        if title:
            body["title"] = title
        if engine:
            body["engine"] = engine
        return self.request_json("POST", "/session/browser/open", body=body)

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
        return self.request_json("POST", "/session/screencast/start", body=body)

    def adopt_screencast(
        self,
        *,
        session_path: str,
        streams: list[dict[str, Any]] | None = None,
        node_ids: list[int] | None = None,
        stream_targets: list[str] | None = None,
        multiple: bool | None = None,
        keeper_managed: bool | None = None,
        socket_path: str | None = None,
        runtime_dir: str | None = None,
        keeper_pid: int | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"session_path": session_path}
        if streams is not None:
            body["streams"] = streams
        if node_ids is not None:
            body["node_ids"] = node_ids
        if stream_targets is not None:
            body["stream_targets"] = stream_targets
        if multiple is not None:
            body["multiple"] = multiple
        if keeper_managed is not None:
            body["keeper_managed"] = keeper_managed
        if socket_path:
            body["socket_path"] = socket_path
        if runtime_dir:
            body["runtime_dir"] = runtime_dir
        if keeper_pid is not None:
            body["keeper_pid"] = keeper_pid
        return self.request_json("POST", "/session/screencast/adopt", body=body)

    def stop_screencast(self) -> dict[str, Any]:
        return self.request_json("POST", "/session/screencast/stop")

    def screencast_status(self) -> dict[str, Any]:
        return self.request_json("GET", "/session/screencast/status")

    def stop_session(self, session_id: str) -> dict[str, Any]:
        return self.request_json("POST", f"/session/{session_id}/stop")

    def sampler_start(
        self,
        *,
        interval_s: float = 5.0,
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
        return self.request_json(
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
        return self.request_json("POST", "/sampler/stop")

    def sampler_status(self) -> dict[str, Any]:
        return self.request_json("GET", "/sampler/status")

    def diagnose_control(self, *, display: str | None = None) -> dict[str, Any]:
        suffix = f"?display={display}" if display else ""
        return self.request_json("GET", f"/diagnostics/control{suffix}")

    def list_controls(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.request_json("POST", "/controls/list", body=body or {})

    def find_controls(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.request_json("POST", "/controls/find", body=body)

    def invoke_control(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.request_json("POST", "/control/invoke", body=body)

    def focus_control(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.request_json("POST", "/control/focus", body=body)

    def set_control_value(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.request_json("POST", "/control/set-value", body=body)

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
        return self.request_json("POST", "/capture/frame", body=body)

    def capture_png_bytes(self, **kwargs: Any) -> tuple[bytes, dict[str, Any]]:
        payload = self.capture_frame(**kwargs)
        encoded = payload.get("png_base64")
        if not encoded:
            raise VDisplayError("agent capture response missing png_base64")
        meta = dict(payload)
        meta.pop("png_base64", None)
        return base64.b64decode(encoded), meta

    def adopt_window(self, **kwargs: Any) -> dict[str, Any]:
        return self.request_json("POST", "/window/adopt", body=kwargs)

    def release_window(self, **kwargs: Any) -> dict[str, Any]:
        return self.request_json("POST", "/window/release", body=kwargs)


__all__ = ["AgentClientApiMixin"]
