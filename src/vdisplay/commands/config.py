from __future__ import annotations

import argparse

from .io import print_json


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("config", help="Project vdisplay.yaml config and metadata layout")
    parser.add_argument(
        "--project",
        default=".",
        help="Project root containing vdisplay.yaml (default: .)",
    )
    subparsers = parser.add_subparsers(dest="config_command")

    show = subparsers.add_parser("show", help="Show merged automation config (default)")
    show.set_defaults(config_command="show")

    clear = subparsers.add_parser(
        "clear",
        help="Delete all runtime artifacts under .vdisplay/ (sessions, captures, broker log)",
    )
    clear.add_argument(
        "--dry-run",
        action="store_true",
        help="List what would be removed without deleting",
    )
    clear.set_defaults(config_command="clear")

    parser.set_defaults(func=handle, config_command="show")


def handle(args: argparse.Namespace) -> int:
    from ..application.project_config import clear_metadata_dir, ensure_metadata_layout, load_project_config

    command = getattr(args, "config_command", "show") or "show"

    if command == "clear":
        result = clear_metadata_dir(
            args.project,
            dry_run=bool(getattr(args, "dry_run", False)),
        )
        print_json(result)
        return 0 if result.get("ok") else 1

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
