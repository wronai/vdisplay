from __future__ import annotations

import argparse
import sys

from .commands import register_all
from .exceptions import BackendNotAvailableError, VDisplayError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vdisplay",
        description="Cross-platform virtual display orchestration",
    )
    sub = parser.add_subparsers(dest="kind", required=True)
    register_all(sub)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return args.func(args)
    except (VDisplayError, BackendNotAvailableError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
