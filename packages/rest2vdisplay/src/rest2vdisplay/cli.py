from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(prog="rest2vdisplay")
    sub = parser.add_subparsers(dest="action", required=True)
    serve = sub.add_parser("serve")
    serve.add_argument("--port", type=int, default=8216)
    serve.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    if args.action == "serve":
        import uvicorn
        from rest2vdisplay.app import create_app

        uvicorn.run(create_app(), host=args.host, port=args.port)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
