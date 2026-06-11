from __future__ import annotations

import argparse
import sys

from .commands import register_all
from .commands.session import add_root_session_args
from .application.session_context import apply_cli_session_args
from .application.env_loader import load_project_env
from .exceptions import BackendNotAvailableError, VDisplayError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vdisplay",
        description="Cross-platform virtual display orchestration",
    )
    add_root_session_args(parser)
    sub = parser.add_subparsers(dest="kind", required=True)
    register_all(sub)
    return parser


def main(argv: list[str] | None = None) -> int:
    load_project_env(".")
    parser = build_parser()
    args = parser.parse_args(argv)
    apply_cli_session_args(args)

    try:
        return args.func(args)
    except (VDisplayError, BackendNotAvailableError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
