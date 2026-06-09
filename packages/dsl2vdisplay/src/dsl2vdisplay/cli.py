from __future__ import annotations

import argparse
import json
import sys

from dsl2vdisplay.bus import dispatch, execute_dsl_line
from dsl2vdisplay.schema_registry import all_schemas

_SUBCOMMANDS = frozenset({"exec", "run", "validate-schema", "shell"})


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in _SUBCOMMANDS:
        return _main_subcommand(argv)
    return _main_legacy(argv)


def _main_legacy(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="dsl2vdisplay")
    parser.add_argument("-c", "--command", help="DSL command line")
    parser.add_argument("script", nargs="?", help="DSL script file")
    args = parser.parse_args(argv)

    if args.command:
        result = execute_dsl_line(args.command)
        print(result.output or json.dumps(result.to_dict(), indent=2))
        return 0 if result.ok else 1
    if args.script:
        for line in open(args.script, encoding="utf-8"):
            if not line.strip() or line.strip().startswith("#"):
                continue
            result = execute_dsl_line(line)
            print(result.output or json.dumps(result.to_dict(), indent=2))
            if not result.ok:
                return 1
        return 0
    parser.print_help()
    return 2


def _main_subcommand(argv: list[str]) -> int:
    cmd = argv[0]
    rest = argv[1:]
    if cmd == "exec":
        parser = argparse.ArgumentParser(prog="dsl2vdisplay exec")
        parser.add_argument("command")
        args = parser.parse_args(rest)
        result = execute_dsl_line(args.command)
        print(result.output or json.dumps(result.to_dict(), indent=2))
        return 0 if result.ok else 1
    if cmd == "validate-schema":
        schemas = all_schemas()
        print(json.dumps({"verbs": list(schemas.keys()), "count": len(schemas)}, indent=2))
        return 0
    if cmd == "shell":
        print("dsl2vdisplay shell — type DSL lines, Ctrl-D to exit")
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            result = dispatch(line)
            print(result.output or json.dumps(result.to_dict(), indent=2))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
