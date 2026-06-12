from __future__ import annotations

import json
from typing import Any


def create_server():
    from mcp.server.fastmcp import FastMCP
    from dsl2vdisplay import dispatch, execute_dsl_line
    from vdisplay.agent_config import resolve_agent_url

    app = FastMCP("vdisplay")

    def _client_or_error():
        url = resolve_agent_url()
        if not url:
            return None, {
                "ok": False,
                "error": "VDISPLAY_AGENT_URL not set. Start agent: vdisplay-agent serve",
            }
        from vdisplay.client import AgentClient

        return AgentClient(url), None

    @app.tool()
    def vdisplay_agent_status() -> dict[str, Any]:
        """Check vdisplay-agent broker connectivity (requires VDISPLAY_AGENT_URL)."""
        client, error = _client_or_error()
        if error:
            return error

        health = client.health()
        caps = client.capabilities()
        return {"ok": True, "health": health, "capabilities": caps}

    @app.tool()
    def vdisplay_run_command(command: str) -> dict[str, Any]:
        """Execute a single vdisplay DSL command (via agent when VDISPLAY_AGENT_URL is set)."""
        return execute_dsl_line(command).to_dict()

    @app.tool()
    def vdisplay_run_dsl(script: str) -> list[dict[str, Any]]:
        """Execute vdisplay DSL script (one command per line)."""
        results = []
        for line in script.splitlines():
            if not line.strip() or line.strip().startswith("#"):
                continue
            results.append(dispatch(line).to_dict())
        return results

    @app.tool()
    def vdisplay_to_dsl(prompt: str) -> str:
        """Convert NL hint to DSL line (no side effects)."""
        try:
            from nlp2vdisplay.to_dsl import nl_to_dsl
            return nl_to_dsl(prompt)
        except ImportError:
            return "INFO"

    @app.tool()
    def vdisplay_screencast_start(
        interactive: bool = True,
        timeout_s: float = 120.0,
    ) -> dict[str, Any]:
        """Start persistent portal ScreenCast on vdisplay-agent (Wayland host capture)."""
        client, error = _client_or_error()
        if error:
            return error

        return client.start_screencast(interactive=interactive, timeout_s=timeout_s)

    @app.tool()
    def vdisplay_screencast_stop() -> dict[str, Any]:
        """Stop active portal ScreenCast session on vdisplay-agent."""
        client, error = _client_or_error()
        if error:
            return error

        return client.stop_screencast()

    @app.tool()
    def vdisplay_screencast_status() -> dict[str, Any]:
        """Return portal ScreenCast session state from vdisplay-agent."""
        client, error = _client_or_error()
        if error:
            return error

        return client.screencast_status()

    @app.tool()
    def vdisplay_capture_frame(
        output: str,
        source: str | None = None,
        display: str | None = None,
    ) -> dict[str, Any]:
        """Capture a desktop frame through vdisplay-agent into an output PNG path."""
        client, error = _client_or_error()
        if error:
            return error
        return client.capture_frame(output=output, source=source, display=display)

    @app.tool()
    def vdisplay_windows(
        display: str | None = None,
        match_app: str | None = None,
    ) -> dict[str, Any]:
        """List visible windows through vdisplay-agent."""
        client, error = _client_or_error()
        if error:
            return error
        return client.windows(display=display, match_app=match_app, apps_only=True)

    @app.tool()
    def vdisplay_outputs(display: str | None = None) -> dict[str, Any]:
        """List monitors/outputs through vdisplay-agent."""
        client, error = _client_or_error()
        if error:
            return error
        return client.outputs(display=display)

    @app.tool()
    def vdisplay_controls_find(query: str, backend: str = "auto") -> dict[str, Any]:
        """Find semantic desktop controls through vdisplay-agent."""
        client, error = _client_or_error()
        if error:
            return error
        return client.find_controls({"query": query, "backend": backend})

    @app.tool()
    def vdisplay_control_focus(target_id: str, backend: str = "auto") -> dict[str, Any]:
        """Focus a desktop control by id through vdisplay-agent."""
        client, error = _client_or_error()
        if error:
            return error
        return client.focus_control({"target_id": target_id, "backend": backend})

    @app.tool()
    def vdisplay_control_set_value(target_id: str, text: str, backend: str = "auto") -> dict[str, Any]:
        """Set text/value on a desktop control by id through vdisplay-agent."""
        client, error = _client_or_error()
        if error:
            return error
        return client.set_control_value({"target_id": target_id, "text": text, "backend": backend})

    @app.tool()
    def vdisplay_browser_bridge_status() -> dict[str, Any]:
        """Return Electron/browser pushed-frame bridge status from vdisplay-agent."""
        client, error = _client_or_error()
        if error:
            return error
        return client.browser_bridge_status()

    return app
