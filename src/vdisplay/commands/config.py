from __future__ import annotations

import argparse

from .io import print_json


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("config", help="Show project vdisplay.yaml automation config")
    parser.add_argument(
        "--project",
        default=".",
        help="Project root containing vdisplay.yaml (default: .)",
    )
    parser.set_defaults(func=handle)


def handle(args: argparse.Namespace) -> int:
    from ..application.project_config import ensure_metadata_layout, load_project_config

    config = load_project_config(args.project)
    base = ensure_metadata_layout(args.project, config)
    print_json(
        {
            "ok": True,
            "config": config.to_dict(),
            "metadata_dir": str(base),
            "effective_config": str(base / "config" / "vdisplay.effective.json"),
        }
    )
    return 0
