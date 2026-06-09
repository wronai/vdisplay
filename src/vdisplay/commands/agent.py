from __future__ import annotations

import argparse
import os

from ..exceptions import VDisplayError
from .io import print_json


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("agent", help="Local vdisplay-agent broker (install once, many clients)")
    agent_sub = parser.add_subparsers(dest="action", required=True)

    agent_serve = agent_sub.add_parser("serve", help="Start localhost broker on 127.0.0.1:8765")
    agent_serve.add_argument("--host", default=None, help="Bind host (default: 127.0.0.1)")
    agent_serve.add_argument("--port", type=int, default=None, help="Bind port (default: 8765)")
    agent_serve.set_defaults(func=handle)

    agent_health = agent_sub.add_parser("health", help="Check agent health via VDISPLAY_AGENT_URL")
    agent_health.set_defaults(func=handle)


def handle(args: argparse.Namespace) -> int:
    if args.action == "serve":
        try:
            import uvicorn
            from vdisplay_agent.server import create_app
        except ImportError as exc:
            raise VDisplayError(
                "Install agent: pip install -e packages/vdisplay-agent[serve]"
            ) from exc
        host = args.host or os.environ.get("VDISPLAY_AGENT_HOST", "127.0.0.1")
        port = args.port or int(os.environ.get("VDISPLAY_AGENT_PORT", "8765"))
        uvicorn.run(create_app(), host=host, port=port)
        return 0
    if args.action == "health":
        from ..agent_config import resolve_agent_url
        from ..client import AgentClient

        url = resolve_agent_url()
        if not url:
            raise VDisplayError("Set VDISPLAY_AGENT_URL (e.g. http://127.0.0.1:8765)")
        print_json(AgentClient(url).health())
        return 0
    raise VDisplayError(f"unsupported agent action: {args.action}")
