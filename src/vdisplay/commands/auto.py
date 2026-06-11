from __future__ import annotations

import argparse

from ..exceptions import VDisplayError
from .io import print_json


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser(
        "auto",
        help="Run desktop automation tasks from planfile.yaml or .planfile ticket queue",
    )
    parser.add_argument(
        "--project",
        default=".",
        help="Project root containing planfile.yaml and/or .planfile/ (default: .)",
    )
    parser.add_argument(
        "--planfile",
        default=None,
        help="Path to planfile.yaml (default: <project>/planfile.yaml)",
    )
    parser.add_argument(
        "--source",
        choices=["auto", "yaml", "tickets"],
        default="auto",
        help="Task source: planfile.yaml automation tasks, .planfile tickets, or auto",
    )
    parser.add_argument(
        "--assigned-to",
        default="vdisplay-auto",
        help="planfile ticket assignee when using .planfile queue",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve and print the next command without executing",
    )

    auto_sub = parser.add_subparsers(dest="action", required=True)

    run = auto_sub.add_parser("run", help="Run all runnable tasks until queue is empty")
    run.add_argument(
        "--max",
        type=int,
        default=0,
        help="Stop after N tasks (0 = unlimited)",
    )
    run.set_defaults(func=handle)

    once = auto_sub.add_parser("once", help="Run a single next task")
    once.set_defaults(func=handle)

    listing = auto_sub.add_parser("list", help="List pending automation tasks")
    listing.set_defaults(func=handle)

    nxt = auto_sub.add_parser("next", help="Show the next runnable task")
    nxt.set_defaults(func=handle)


def handle(args: argparse.Namespace) -> int:
    from ..application.auto.runner import list_auto_tasks, run_auto_loop, run_auto_once
    from ..application.auto.tasks import ensure_auto_dependencies

    ensure_auto_dependencies(source=args.source)

    list_common = {
        "project": args.project,
        "planfile": args.planfile,
        "source": args.source,
    }
    run_common = {
        **list_common,
        "assigned_to": args.assigned_to,
        "dry_run": bool(getattr(args, "dry_run", False)),
    }
    action = args.action
    if action == "list":
        print_json(list_auto_tasks(**list_common))
        return 0
    if action == "next":
        payload = list_auto_tasks(**list_common)
        print_json({"ok": True, "next": payload.get("next"), "count": payload.get("count", 0)})
        return 0
    if action == "once":
        result = run_auto_once(**run_common)
        print_json(result.to_dict())
        return 0 if result.ok else 1
    if action == "run":
        result = run_auto_loop(max_tasks=int(getattr(args, "max", 0) or 0), **run_common)
        print_json(result.to_dict())
        return 0 if result.ok else 1
    raise VDisplayError(f"unsupported auto action: {action}")
