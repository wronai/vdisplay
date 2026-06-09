from __future__ import annotations

import argparse
import sys


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("nlp", help="Natural language → DSL → JSON (same as nlp2vdisplay)")
    parser.add_argument("prompt", help="Natural language request")
    parser.add_argument("--dsl-only", action="store_true", help="Print DSL line only")
    parser.set_defaults(func=handle)


def handle(args: argparse.Namespace) -> int:
    from ..nlp import run_nl_prompt

    line, output, code = run_nl_prompt(args.prompt, dsl_only=args.dsl_only)
    if args.dsl_only:
        print(output)
    else:
        print(f"# dsl: {line}", file=sys.stderr)
        print(output)
    return code
