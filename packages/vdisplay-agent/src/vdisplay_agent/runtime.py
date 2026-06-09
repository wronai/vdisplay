"""In-process session registry — only the agent process touches capture backends."""

from __future__ import annotations

import base64
import os
import platform
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from vdisplay import MirrorSession, VirtualDisplaySession, WindowRelaySession, platform_summary
from vdisplay.capture.host import capture_all_monitors, capture_host_to_file
from vdisplay.capture.providers.engine import list_capture_providers
from vdisplay.discovery import diagnose_display, resolve_host_display
from vdisplay.exceptions import VDisplayError
from vdisplay.application.services import discovery


@dataclass
class SessionRecord:
    session_id: str
    kind: str
    handle: Any
    started: bool = True


@dataclass
class AgentRuntime:
    """Privileged runtime: owns sessions and native capture providers."""

    sessions: dict[str, SessionRecord] = field(default_factory=dict)
    relay: WindowRelaySession | None = None

    def platform_capabilities(self) -> dict[str, Any]:
        session_type = os.environ.get("XDG_SESSION_TYPE", "unknown")
        capture_providers = list_capture_providers(resolve_host_display(None))
        from vdisplay.capture.portal_screencast import get_active_screencast

        screencast = get_active_screencast()
        return {
            "platform": platform.system().lower(),
            "python": platform.python_version(),
            "session_type": session_type,
            "session_modes": ["virtual", "mirror", "relay", "screencast"],
            "capture_sources": [row["name"] for row in capture_providers if row.get("available") == "true"],
            "capture_providers": capture_providers,
            "screencast": {
                "supported": session_type == "wayland",
                "active": screencast is not None and screencast.active,
                "ready": screencast is not None and screencast.is_ready,
            },
            "window_relay": sys.platform.startswith("linux"),
            "input_control": sys.platform.startswith("linux"),
            "requires_admin_install": False,
            "requires_user_runtime_prompt": session_type == "wayland",
            "supports_protected_content": False,
            "broker": "vdisplay-agent",
            **platform_summary(),
        }

    def diagnostics(self, *, display: str | None = None) -> dict[str, Any]:
        resolved = resolve_host_display(display)
        payload = diagnose_display(resolved)
        payload["agent_sessions"] = len(self.sessions)
        payload["relay_active"] = self.relay is not None
        payload["capabilities"] = self.platform_capabilities()
        return payload

    def outputs(self, *, display: str | None = None, include_all: bool = True) -> dict[str, Any]:
        from vdisplay.discovery import list_outputs, resolve_host_display

        resolved = resolve_host_display(display)
        monitors = list_outputs(resolved, enrich_nl=False, apps_only=not include_all)
        return {
            "requested_display": display or os.environ.get("DISPLAY"),
            "resolved_display": resolved,
            "monitor_count": len(monitors),
            "monitors": monitors,
        }

    def list_windows(self, **filters: Any) -> dict[str, Any]:
        display = filters.get("display")
        include_all = str(filters.get("include_all", "true")).lower() not in {"0", "false", "no"}
        apps_only_raw = filters.get("apps_only")
        apps_only = None
        if apps_only_raw is not None:
            apps_only = str(apps_only_raw).lower() in {"1", "true", "yes"}
        match_pid = filters.get("match_pid")
        if match_pid is not None and str(match_pid).strip():
            match_pid = int(match_pid)
        else:
            match_pid = None
        return discovery.list_windows_local(
            display,
            include_all=include_all,
            apps_only=apps_only,
            min_width=int(filters.get("min_width") or 0),
            min_height=int(filters.get("min_height") or 0),
            match_class=filters.get("match_class") or filters.get("wm_class"),
            match_pid=match_pid,
            match_app=filters.get("match_app") or filters.get("app"),
        )

    def start_virtual(
        self,
        *,
        width: int = 1280,
        height: int = 720,
        display: str = ":99",
    ) -> dict[str, Any]:
        session = VirtualDisplaySession.create(width=width, height=height, display=display)
        session.start()
        session_id = f"virt-{uuid.uuid4().hex[:12]}"
        self.sessions[session_id] = SessionRecord(session_id=session_id, kind="virtual", handle=session)
        return {
            "ok": True,
            "session_id": session_id,
            "mode": "virtual",
            "info": session.info(),
            "capabilities": session.capabilities(),
        }

    def start_mirror(
        self,
        *,
        source: str = "primary",
        target: str | None = None,
        display: str | None = None,
    ) -> dict[str, Any]:
        session = MirrorSession.create(source=source, target=target, display=display)
        session.start()
        session_id = f"mir-{uuid.uuid4().hex[:12]}"
        self.sessions[session_id] = SessionRecord(session_id=session_id, kind="mirror", handle=session)
        return {
            "ok": True,
            "session_id": session_id,
            "mode": "mirror",
            "info": session.info(),
            "capabilities": session.capabilities(),
        }

    def start_relay(self, *, display: str | None = None) -> dict[str, Any]:
        if self.relay is None:
            self.relay = WindowRelaySession.create(display=display)
            self.relay.start()
        session_id = f"relay-{uuid.uuid4().hex[:12]}"
        self.sessions[session_id] = SessionRecord(session_id=session_id, kind="relay", handle=self.relay)
        return {
            "ok": True,
            "session_id": session_id,
            "mode": "relay",
            "info": self.relay.info(),
            "capabilities": self.relay.capabilities(),
        }

    def start_screencast(self, *, interactive: bool = True, timeout_s: float = 120.0) -> dict[str, Any]:
        from vdisplay.capture.portal_screencast import start_screencast_session

        session = start_screencast_session(interactive=interactive, timeout_s=timeout_s)
        return {"ok": True, **session.status()}

    def stop_screencast(self) -> dict[str, Any]:
        from vdisplay.capture.portal_screencast import stop_screencast_session

        return stop_screencast_session()

    def screencast_status(self) -> dict[str, Any]:
        from vdisplay.capture.portal_screencast import get_active_screencast

        session = get_active_screencast()
        if session is None:
            return {"ok": True, "active": False, "ready": False}
        return {"ok": True, **session.status()}

    def stop_session(self, session_id: str) -> dict[str, Any]:
        record = self.sessions.pop(session_id, None)
        if record is None:
            raise VDisplayError(f"unknown session_id: {session_id}")
        if record.kind == "relay" and record.handle is self.relay:
            self.relay.stop()
            self.relay = None
        else:
            record.handle.stop()
        return {"ok": True, "session_id": session_id, "stopped": True}

    def capture_frame(self, body: dict[str, Any]) -> dict[str, Any]:
        session_id = body.get("session_id")
        if session_id:
            record = self.sessions.get(str(session_id))
            if record is None:
                raise VDisplayError(f"unknown session_id: {session_id}")
            png = record.handle.screenshot_bytes()
            result: dict[str, Any] = {
                "ok": True,
                "session_id": session_id,
                "mode": record.kind,
                "png_base64": base64.b64encode(png).decode("ascii"),
                "bytes": len(png),
            }
            output = body.get("output") or body.get("path")
            if output:
                out = Path(output).expanduser()
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(png)
                result["path"] = str(out.resolve())
            return result

        if body.get("all_monitors"):
            out_dir = body.get("out_dir") or str(Path("/tmp/vdisplay-agent-captures"))
            captures = capture_all_monitors(
                display=body.get("display"),
                out_dir=out_dir,
                target=body.get("target"),
                prefer_mirror=bool(body.get("prefer_mirror")),
            )
            return {"ok": True, "out_dir": out_dir, "captures": captures, "count": len(captures)}

        output = body.get("output") or body.get("path")
        if not output:
            raise VDisplayError("capture requires session_id, all_monitors, or output path")

        meta = capture_host_to_file(
            output,
            monitor=int(body.get("monitor") or 1),
            display=body.get("display"),
            source=body.get("source"),
            target=body.get("target"),
            prefer_mirror=bool(body.get("prefer_mirror")),
        )
        png = Path(meta["path"]).read_bytes()
        meta["ok"] = True
        meta["png_base64"] = base64.b64encode(png).decode("ascii")
        return meta

    def adopt_window(self, body: dict[str, Any]) -> dict[str, Any]:
        relay = self._relay_session(body.get("session_id"))
        window_id = relay.adopt_window(
            match_title=body.get("match_title") or body.get("title"),
            window_id=body.get("window_id"),
            match_class=body.get("match_class") or body.get("wm_class"),
            match_pid=body.get("match_pid") or body.get("pid"),
            match_app=body.get("match_app") or body.get("app"),
            target=body.get("target") or "offscreen",
        )
        return {"ok": True, "window_id": window_id, "adopted": relay.list_adopted()}

    def release_window(self, body: dict[str, Any]) -> dict[str, Any]:
        relay = self._relay_session(body.get("session_id"))
        window_id = relay.release_window(
            match_title=body.get("match_title") or body.get("title"),
            window_id=body.get("window_id"),
            match_class=body.get("match_class") or body.get("wm_class"),
            match_pid=body.get("match_pid") or body.get("pid"),
            match_app=body.get("match_app") or body.get("app"),
        )
        return {"ok": True, "window_id": window_id, "adopted": relay.list_adopted()}

    def _relay_session(self, session_id: str | None) -> WindowRelaySession:
        if session_id:
            record = self.sessions.get(str(session_id))
            if record is None or record.kind != "relay":
                raise VDisplayError(f"relay session not found: {session_id}")
            return record.handle
        if self.relay is None:
            self.relay = WindowRelaySession.create()
            self.relay.start()
        return self.relay

    def shutdown(self) -> None:
        from vdisplay.capture.portal_screencast import stop_screencast_session

        stop_screencast_session()
        for session_id in list(self.sessions):
            try:
                self.stop_session(session_id)
            except VDisplayError:
                pass
        if self.relay is not None:
            self.relay.stop()
            self.relay = None
