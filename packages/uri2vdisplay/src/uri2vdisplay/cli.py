from __future__ import annotations

import argparse
import json
import sys

from dsl2vdisplay import dispatch
from uri2vdisplay.decode import uri_to_dsl


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="uri2vdisplay")
    sub = parser.add_subparsers(dest="action", required=True)
    dec = sub.add_parser("decode")
    dec.add_argument("--uri", required=True)
    run = sub.add_parser("run")
    run.add_argument("--uri", required=True)
    args = parser.parse_args(argv)

    line = uri_to_dsl(args.uri)
    if args.action == "decode":
        print(line)
        return 0
    result = dispatch(line)
    print(result.output or json.dumps(result.to_dict(), indent=2))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
