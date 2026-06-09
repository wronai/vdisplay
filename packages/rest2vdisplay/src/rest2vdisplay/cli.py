from __future__ import annotations

import argparse
import os


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="rest2vdisplay",
        description="REST adapter for vdisplay (routes DSL through vdisplay-agent when configured)",
    )
    sub = parser.add_subparsers(dest="action", required=True)
    serve = sub.add_parser("serve")
    serve.add_argument("--port", type=int, default=8216)
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument(
        "--agent-url",
        default=os.environ.get("VDISPLAY_AGENT_URL"),
        help="Broker URL (default: VDISPLAY_AGENT_URL env)",
    )
    args = parser.parse_args()

    if args.action == "serve":
        import uvicorn
        from rest2vdisplay.app import create_app

        if args.agent_url:
            os.environ["VDISPLAY_AGENT_URL"] = args.agent_url.rstrip("/")
        uvicorn.run(create_app(agent_url=args.agent_url), host=args.host, port=args.port)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
