from __future__ import annotations

import argparse
import os


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="vdisplay-agent", description="Local vdisplay broker")
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="Start localhost REST broker")
    serve.add_argument("--host", default=os.environ.get("VDISPLAY_AGENT_HOST", "127.0.0.1"))
    serve.add_argument("--port", type=int, default=int(os.environ.get("VDISPLAY_AGENT_PORT", "8765")))
    serve.add_argument("--reload", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "serve":
        try:
            import uvicorn
        except ImportError as exc:
            raise SystemExit(
                "Install serve extras: pip install -e packages/vdisplay-agent[serve]"
            ) from exc
        from vdisplay_agent.server import create_app

        app = create_app()
        uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
