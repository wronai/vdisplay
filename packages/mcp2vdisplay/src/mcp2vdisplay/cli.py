from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(prog="mcp2vdisplay")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("serve")
    args = parser.parse_args()
    if args.action == "serve":
        create_server().run()
        return 0
    return 2


def create_server():
    from mcp2vdisplay.server import create_server as _create
    return _create()


if __name__ == "__main__":
    raise SystemExit(main())
