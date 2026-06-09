from __future__ import annotations

import argparse
import json
import sys

from dsl2vdisplay import dispatch
from nlp2vdisplay.to_dsl import nl_to_dsl


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="nlp2vdisplay")
    sub = parser.add_subparsers(dest="action", required=True)
    to_dsl = sub.add_parser("to-dsl")
    to_dsl.add_argument("prompt")
    apply_p = sub.add_parser("apply")
    apply_p.add_argument("prompt")
    args = parser.parse_args(argv)

    line = nl_to_dsl(args.prompt)
    if args.action == "to-dsl":
        print(line)
        return 0
    result = dispatch(line)
    print(result.output or json.dumps(result.to_dict(), indent=2))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
