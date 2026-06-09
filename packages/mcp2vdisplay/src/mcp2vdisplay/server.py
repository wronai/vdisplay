from __future__ import annotations

import json
from typing import Any


def create_server():
    from mcp.server.fastmcp import FastMCP
    from dsl2vdisplay import dispatch, execute_dsl_line

    app = FastMCP("vdisplay")

    @app.tool()
    def vdisplay_run_command(command: str) -> dict[str, Any]:
        """Execute a single vdisplay DSL command."""
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

    return app
