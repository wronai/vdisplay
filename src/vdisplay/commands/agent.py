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

    sc_parser = agent_sub.add_parser(
        "screencast",
        help="Portal ScreenCast session on the agent (Wayland host capture)",
    )
    sc_sub = sc_parser.add_subparsers(dest="sc_action", required=True)

    sc_start = sc_sub.add_parser("start", help="Start persistent ScreenCast (one portal consent)")
    sc_start.add_argument(
        "--no-interactive",
        action="store_true",
        help="Do not show portal UI (fails if consent already granted)",
    )
    sc_start.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="Portal dialog timeout in seconds (default: 120)",
    )
    sc_start.add_argument(
        "--single-monitor",
        action="store_true",
        help="Capture one monitor only (portal: pick a single screen)",
    )
    sc_start.add_argument(
        "--all-monitors",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    sc_start.set_defaults(func=handle, sc_action="start")

    sc_stop = sc_sub.add_parser("stop", help="Stop active ScreenCast session")
    sc_stop.set_defaults(func=handle, sc_action="stop")

    sc_status = sc_sub.add_parser("status", help="Show ScreenCast session state")
    sc_status.set_defaults(func=handle, sc_action="status")

    browser_open = agent_sub.add_parser("browser-open", help="Open Playwright browser session on agent")
    browser_open.add_argument("--url", required=True)
    browser_open.add_argument("--session-id", required=True)
    browser_open.add_argument("--headed", action="store_true")
    browser_open.add_argument("--vendor", choices=["chromium", "firefox"])
    browser_open.add_argument("--engine", help="Alias for --vendor")
    browser_open.set_defaults(func=handle)


def _agent_client(*, timeout: float | None = None):
    from ..agent_config import resolve_agent_url
    from ..client import AgentClient

    url = resolve_agent_url(allow_auto=True)
    if not url:
        raise VDisplayError(
            "Set VDISPLAY_AGENT_URL (e.g. http://127.0.0.1:8765) or start: vdisplay-agent serve"
        )
    kwargs: dict[str, float] = {}
    if timeout is not None:
        kwargs["timeout"] = timeout
    return AgentClient(url, **kwargs)


def handle(args: argparse.Namespace) -> int:
    if args.action == "serve":
        return _handle_serve(args)
    if args.action == "health":
        print_json(_agent_client(timeout=5.0).health())
        return 0
    if args.action == "browser-open":
        return _handle_browser_open(args)
    if args.action == "screencast":
        return _handle_screencast(args)
    raise VDisplayError(f"unsupported agent action: {args.action}")


def _handle_serve(args: argparse.Namespace) -> int:
    try:
        import uvicorn
        from vdisplay_agent.server import create_app
    except ImportError as exc:
        raise VDisplayError(
            "Install agent: pip install -e packages/vdisplay-agent[serve]"
        ) from exc
    from vdisplay_agent.serve_port import ensure_broker_port_free

    host = args.host or os.environ.get("VDISPLAY_AGENT_HOST", "127.0.0.1")
    port = args.port or int(os.environ.get("VDISPLAY_AGENT_PORT", "8765"))
    try:
        ensure_broker_port_free(host, port)
    except RuntimeError as exc:
        raise VDisplayError(str(exc)) from exc
    print(
        "Wayland host capture: run `vdisplay agent screencast start` after each serve",
        file=__import__("sys").stderr,
    )
    uvicorn.run(create_app(), host=host, port=port)
    return 0


def _handle_browser_open(args: argparse.Namespace) -> int:
    from ..agent_config import resolve_agent_url
    from ..application.services import session as session_svc

    engine = getattr(args, "vendor", None) or getattr(args, "engine", None)
    headless = not getattr(args, "headed", False)
    if resolve_agent_url(allow_auto=True):
        print_json(
            _agent_client().browser_open(
                url=args.url,
                session_id=args.session_id,
                headless=headless,
                engine=engine,
            )
        )
    else:
        print_json(
            session_svc.browser_open(
                url=args.url,
                session_id=args.session_id,
                headless=headless,
                engine=engine,
            )
        )
    return 0


def _handle_screencast(args: argparse.Namespace) -> int:
    fast = _agent_client(timeout=5.0)
    if args.sc_action == "start":
        status = fast.screencast_status()
        if status.get("active") and status.get("ready"):
            print_json({**status, "ok": True, "reused": True})
            return 0
        import sys

        print(
            "vdisplay: waiting for GNOME Screen Recording portal — choose All Screens",
            file=sys.stderr,
        )
        multiple = False if args.single_monitor else True
        if args.no_interactive:
            print_json(
                _agent_client(timeout=120.0).start_screencast(
                    interactive=False,
                    timeout_s=args.timeout,
                    multiple=multiple,
                )
            )
            return 0

        from ..application.services.screencast_cli import start_screencast_via_agent

        print_json(
            start_screencast_via_agent(
                _agent_client(timeout=120.0),
                interactive=True,
                timeout_s=args.timeout,
                multiple=multiple,
            )
        )
        return 0
    if args.sc_action == "stop":
        print_json(fast.stop_screencast())
        return 0
    if args.sc_action == "status":
        print_json(fast.screencast_status())
        return 0
    raise VDisplayError(f"unsupported screencast action: {args.sc_action}")
