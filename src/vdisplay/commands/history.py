"""Inspect and analyze automation history under ``.vdisplay/**``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from .io import print_json


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser(
        "history",
        help="List and analyze event history from .vdisplay/ (runs, sessions, broker, observe)",
    )

    history_sub = parser.add_subparsers(dest="history_action", required=True)

    list_parser = history_sub.add_parser("list", help="List runs, sessions, and artifact counts")
    list_parser.add_argument(
        "--root",
        default=".vdisplay",
        help="Metadata root (default: .vdisplay)",
    )
    list_parser.add_argument("--limit", type=int, default=20, help="Max runs/sessions to include")
    list_parser.set_defaults(func=handle_list)

    show_parser = history_sub.add_parser("show", help="Show one run or session in detail")
    show_parser.add_argument(
        "--root",
        default=".vdisplay",
        help="Metadata root (default: .vdisplay)",
    )
    show_parser.add_argument("--run", dest="run_id", help="Auto run id (runs/{id}/)")
    show_parser.add_argument("--session", dest="session_dir", help="Audit session directory")
    show_parser.add_argument("--latest", action="store_true", help="Show latest auto run")
    show_parser.set_defaults(func=handle_show)

    analyze_parser = history_sub.add_parser(
        "analyze",
        help="Cross-run analysis: tasks, events, backends, broker errors, observe artifacts",
    )
    analyze_parser.add_argument(
        "--root",
        default=".vdisplay",
        help="Metadata root (default: .vdisplay)",
    )
    analyze_parser.add_argument("--limit", type=int, default=50, help="Max runs/sessions in report")
    analyze_parser.add_argument(
        "--format",
        choices=("json", "summary"),
        default="json",
        help="Output format (default: json)",
    )
    analyze_parser.set_defaults(func=handle_analyze)

    events_parser = history_sub.add_parser("events", help="Timeline of domain events from index.jsonl")
    events_parser.add_argument(
        "--root",
        default=".vdisplay",
        help="Metadata root (default: .vdisplay)",
    )
    events_parser.add_argument("--run", dest="run_id", help="Limit to run session (runs/{id}/session)")
    events_parser.add_argument("--session", dest="session_dir", help="Audit session directory")
    events_parser.add_argument("--type", dest="event_type", help="Filter by event_type")
    events_parser.add_argument("--limit", type=int, default=200, help="Max events (default: 200)")
    events_parser.set_defaults(func=handle_events)

    replay_parser = history_sub.add_parser("replay", help="Replay CONTROL_* steps from a recorded session")
    replay_parser.add_argument(
        "--root",
        default=".vdisplay",
        help="Metadata root (default: .vdisplay)",
    )
    replay_parser.add_argument("--session", dest="session_dir", help="Audit session directory")
    replay_parser.add_argument("--run", dest="run_id", help="Use runs/{id}/session")
    replay_parser.add_argument("--dry-run", action="store_true", help="Plan replay without executing")
    replay_parser.set_defaults(func=handle_replay)


def _resolve_root(args: argparse.Namespace) -> Path:
    from ..application.history.loader import resolve_metadata_root

    return resolve_metadata_root(getattr(args, "root", ".vdisplay"))


def _resolve_session_from_args(args: argparse.Namespace) -> Path:
    from ..application.history.loader import discover_session_dirs, resolve_metadata_root

    if getattr(args, "session_dir", None):
        path = Path(args.session_dir).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        if not (path / "session.json").is_file():
            raise SystemExit(f"error: not a session directory: {path}")
        return path

    run_id = getattr(args, "run_id", None)
    if run_id:
        base = resolve_metadata_root(getattr(args, "root", ".vdisplay"))
        path = base / "runs" / run_id / "session"
        if not (path / "session.json").is_file():
            raise SystemExit(f"error: no session for run {run_id}: {path}")
        return path

    sessions = discover_session_dirs(root=resolve_metadata_root(getattr(args, "root", ".vdisplay")))
    if not sessions:
        raise SystemExit("error: no sessions found")
    return sessions[0]


def handle_list(args: argparse.Namespace) -> int:
    from ..application.history.loader import load_history_index

    index = load_history_index(_resolve_root(args))
    limit = max(int(args.limit), 0)
    payload: dict[str, Any] = {
        "root": str(index.root),
        "latest_run_id": index.latest_run_id,
        "counts": {
            "runs": len(index.runs),
            "sessions": len(index.sessions),
            "tasks": len(index.tasks),
            "broker_events": len(index.broker_events),
            "observe_png": index.observe_png_count,
        },
        "runs": [item.to_dict() for item in index.runs[:limit]],
        "sessions": [item.to_dict() for item in index.sessions[:limit]],
    }
    print_json(payload)
    return 0


def handle_show(args: argparse.Namespace) -> int:
    from ..application.history.loader import load_run_detail, load_session_ref
    from ..application.session_recorder import load_session_document, render_readme

    root = _resolve_root(args)

    if args.latest or args.run_id:
        run_id = args.run_id
        if args.latest:
            latest = root / "latest-run.txt"
            if not latest.is_file():
                print("error: latest-run.txt missing", file=sys.stderr)
                return 1
            run_id = latest.read_text(encoding="utf-8").strip()
        detail = load_run_detail(run_id or "", root=root)
        if detail is None:
            print(f"error: run not found: {run_id}", file=sys.stderr)
            return 1
        print_json(detail)
        return 0

    if args.session_dir:
        session_dir = _resolve_session_from_args(args)
        doc = load_session_document(session_dir)
        ref = load_session_ref(session_dir)
        payload = {
            "session": ref.to_dict(),
            "summary": doc.summary,
            "maps": doc.maps,
            "steps": [step.__dict__ for step in doc.steps],
        }
        readme = session_dir / "README.md"
        if readme.is_file():
            payload["readme_path"] = str(readme)
        else:
            payload["readme_preview"] = render_readme(doc)[:2000]
        print_json(payload)
        return 0

    print("error: specify --run, --latest, or --session", file=sys.stderr)
    return 2


def handle_analyze(args: argparse.Namespace) -> int:
    from ..application.history.analyze import analyze_history

    report = analyze_history(_resolve_root(args), run_limit=int(args.limit))
    if args.format == "summary":
        _print_analyze_summary(report)
        return 0
    print_json(report.to_dict())
    return 0


def _print_analyze_summary(report: Any) -> None:
    summary = report.summary
    lines = [
        f"vdisplay history — {report.root}",
        "",
        f"runs: {summary.get('runs', 0)}  sessions: {summary.get('sessions', 0)}  tasks: {summary.get('tasks', 0)}",
        f"tasks ok/failed: {summary.get('tasks_ok', 0)}/{summary.get('tasks_failed', 0)}",
        f"events: {summary.get('events', 0)}  broker errors: {summary.get('broker_errors', 0)}",
        f"latest run: {summary.get('latest_run_id') or '-'}",
        f"observe png: {summary.get('observe_png', 0)}",
        "",
        "top event types:",
    ]
    for name, count in list(report.event_histogram.items())[:8]:
        lines.append(f"  {name}: {count}")
    if report.backends_used:
        lines.extend(["", "backends:"])
        for name, count in list(report.backends_used.items())[:8]:
            lines.append(f"  {name}: {count}")
    if report.broker_errors:
        lines.extend(["", "recent broker errors:"])
        for item in report.broker_errors[-5:]:
            lines.append(f"  [{item.get('ts')}] {item.get('action')}: {item.get('error') or item.get('code')}")
    sys.stdout.write("\n".join(lines) + "\n")


def handle_events(args: argparse.Namespace) -> int:
    from ..application.history.analyze import collect_events

    session_dir = None
    if args.session_dir:
        session_dir = _resolve_session_from_args(args)
    events = collect_events(
        root=_resolve_root(args),
        run_id=args.run_id,
        session_dir=session_dir,
        event_type=args.event_type,
        limit=int(args.limit),
    )
    print_json({"count": len(events), "events": events})
    return 0


def handle_replay(args: argparse.Namespace) -> int:
    from ..application.replay import replay_session

    session_dir = _resolve_session_from_args(args)
    report = replay_session(session_dir, dry_run=bool(args.dry_run))
    print_json({"ok": report.steps_failed == 0, **report.to_dict()})
    return 0 if report.steps_failed == 0 else 1
