from __future__ import annotations

import argparse
import json
import sys

from dsl2vdisplay import dispatch


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cli2vdisplay")
    sub = parser.add_subparsers(dest="action", required=True)
    exec_p = sub.add_parser("exec")
    exec_p.add_argument("command")
    sub.add_parser("shell")
    args = parser.parse_args(argv)

    if args.action == "shell":
        print("cli2vdisplay shell")
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            result = dispatch(line)
            print(result.output or json.dumps(result.to_dict(), indent=2))
        return 0

    result = dispatch(args.command)
    print(result.output or json.dumps(result.to_dict(), indent=2))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
