from __future__ import annotations

import argparse
import sys

from vdisplay.nlp import run_nl_prompt


def main(argv: list[str] | None = None) -> int:
    raw = list(argv if argv is not None else sys.argv[1:])
    if raw and raw[0] not in {"to-dsl", "apply", "-h", "--help"} and not raw[0].startswith("-"):
        raw = ["apply"] + raw

    parser = argparse.ArgumentParser(
        prog="nlp2vdisplay",
        description="Natural language → DSL → vdisplay JSON output",
    )
    sub = parser.add_subparsers(dest="action", required=True)

    to_dsl = sub.add_parser("to-dsl", help="Run NL pipeline (default) or print DSL with --dsl-only")
    to_dsl.add_argument("prompt")
    to_dsl.add_argument("--dsl-only", action="store_true")

    apply_p = sub.add_parser("apply", help="Run NL → DSL → JSON output")
    apply_p.add_argument("prompt")
    apply_p.add_argument("--dsl-only", action="store_true")

    args = parser.parse_args(raw)

    line, output, code = run_nl_prompt(args.prompt, dsl_only=args.dsl_only)

    if args.action == "to-dsl" and args.dsl_only:
        print(output)
    else:
        print(f"# dsl: {line}", file=sys.stderr)
        print(output)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
