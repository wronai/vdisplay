from __future__ import annotations

import argparse
import os
from urllib.parse import urlparse

from vdisplay.application.env_defaults import env_value
from vdisplay.application.env_loader import load_project_env


def _default_serve_port() -> int:
    agent_url = os.environ.get("VDISPLAY_AGENT_URL", "").strip()
    if agent_url:
        parsed = urlparse(agent_url)
        if parsed.port:
            return parsed.port
    port_raw = os.environ.get("VDISPLAY_AGENT_PORT", "").strip()
    if port_raw.isdigit():
        return int(port_raw)
    return 8765


def main(argv: list[str] | None = None) -> int:
    try:
        load_project_env(".")
    except Exception:
        pass
    parser = argparse.ArgumentParser(prog="vdisplay-agent", description="Local vdisplay broker")
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="Start localhost REST broker")
    serve.add_argument("--host", default=env_value("VDISPLAY_AGENT_HOST") or "127.0.0.1")
    serve.add_argument("--port", type=int, default=_default_serve_port())
    serve.add_argument("--reload", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "serve":
        try:
            import uvicorn
        except ImportError as exc:
            raise SystemExit(
                "Install serve extras: pip install -e packages/vdisplay-agent[serve]"
            ) from exc
        from vdisplay_agent.serve_port import ensure_broker_port_free
        from vdisplay_agent.server import create_app

        try:
            ensure_broker_port_free(args.host, args.port)
        except RuntimeError as exc:
            raise SystemExit(str(exc)) from exc

        try:
            from vdisplay.capture.portal_screencast import ensure_portal_session_env, portal_session_env_status

            ensure_portal_session_env()
            ok, hint = portal_session_env_status()
            if not ok:
                print(f"vdisplay-agent: WARN — {hint}", file=__import__("sys").stderr)
        except Exception:
            pass

        print(
            "Wayland host capture: start vdisplay-agent serve from a local GUI terminal "
            "(same session as GNOME), then: vdisplay agent screencast start",
            file=__import__("sys").stderr,
        )
        app = create_app()
        uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
