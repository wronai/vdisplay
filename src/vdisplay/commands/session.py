"""Shared CLI session flags, audit session commands, and CommandRequest helpers."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from ..application.commands import CommandRequest, CommandVerb
from .common import control_selector_kwargs_from_args
from .io import print_json


def add_root_session_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--session",
        action="store_true",
        help="Enable audit session recording under .vdisplay/ (or VDISPLAY_SESSION_DIR)",
    )
    parser.add_argument(
        "--session-id",
        dest="audit_session_id",
        metavar="ID",
        help="Audit session slug (VDISPLAY_SESSION_ID); distinct from control --session-id",
    )


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("session", help="Inspect and export audit session reports")
    session_sub = parser.add_subparsers(dest="session_action", required=True)

    list_parser = session_sub.add_parser("list", help="List recorded sessions under .vdisplay/")
    list_parser.add_argument(
        "--root",
        default=".vdisplay",
        help="Directory containing session folders (default: .vdisplay)",
    )
    list_parser.set_defaults(func=handle_list)

    show_parser = session_sub.add_parser("show", help="Show session README or JSON")
    show_parser.add_argument(
        "--dir",
        dest="session_dir",
        help="Session directory (default: latest under --root)",
    )
    show_parser.add_argument(
        "--root",
        default=".vdisplay",
        help="Search root when --dir is omitted",
    )
    show_parser.add_argument(
        "--format",
        choices=("readme", "json", "summary"),
        default="readme",
        help="Output format (default: readme)",
    )
    show_parser.set_defaults(func=handle_show)

    export_parser = session_sub.add_parser("export", help="Export session directory as zip")
    export_parser.add_argument(
        "--dir",
        dest="session_dir",
        required=True,
        help="Session directory to export",
    )
    export_parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Output .zip path",
    )
    export_parser.set_defaults(func=handle_export)

    reprocess_parser = session_sub.add_parser(
        "reprocess",
        help="Re-extract diagnostics from stored step results and refresh projections",
    )
    reprocess_parser.add_argument(
        "--dir",
        dest="session_dir",
        help="Session directory (default: latest under --root)",
    )
    reprocess_parser.add_argument(
        "--root",
        default=".vdisplay",
        help="Search root when --dir is omitted",
    )
    reprocess_parser.set_defaults(func=handle_reprocess)


def command_request_from_control_args(args: argparse.Namespace, verb: CommandVerb) -> CommandRequest:
    selector = control_selector_kwargs_from_args(args)
    extra: dict[str, Any] = {
        key: value
        for key, value in selector.items()
        if key
        in {
            "dom_css",
            "dom_xpath",
            "vision_anchor",
            "vision_template",
            "vision_anchor_rel",
            "vision_target",
            "vision_min_confidence",
            "map_path",
            "map_scope",
            "map_target",
        }
        and value is not None
    }
    if getattr(args, "preview", False):
        extra["preview"] = True
    if getattr(args, "preview_output", None):
        extra["preview_output"] = args.preview_output
    if getattr(args, "preview_debug", False):
        extra["preview_debug"] = True

    return CommandRequest(
        verb=verb,
        request_source="cli",
        display=getattr(args, "display", None),
        control_selector=selector.get("selector"),
        control_name=selector.get("name"),
        control_role=selector.get("role"),
        control_app=selector.get("app"),
        control_window_id=selector.get("window_id"),
        control_window_title=selector.get("window_title"),
        control_index=int(selector.get("index") or 0),
        control_environment=selector.get("environment"),
        control_text=selector.get("text"),
        control_text_contains=selector.get("text_contains"),
        control_terminal_line=selector.get("terminal_line"),
        control_terminal_col=selector.get("terminal_col"),
        control_session_id=selector.get("session_id"),
        control_backend=getattr(args, "backend", "auto"),
        control_max_depth=int(getattr(args, "max_depth", 8)),
        control_format=getattr(args, "format", "flat"),
        control_verify=bool(getattr(args, "verify", False)),
        control_screenshot_verify=bool(getattr(args, "screenshot_verify", False)),
        control_verify_label=getattr(args, "verify_label", None),
        control_verify_selector=getattr(args, "verify_selector", None),
        control_value=getattr(args, "value", None),
        extra=extra,
    )


def _resolve_session_dir(args: argparse.Namespace) -> Path:
    from ..application.session_recorder import discover_session_dirs

    if getattr(args, "session_dir", None):
        path = Path(args.session_dir).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        if not (path / "session.json").is_file():
            raise SystemExit(f"error: not a session directory: {path}")
        return path

    explicit = os.environ.get("VDISPLAY_SESSION_DIR", "").strip()
    if explicit:
        path = Path(explicit).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        if (path / "session.json").is_file():
            return path

    root = Path(getattr(args, "root", ".vdisplay")).expanduser()
    if not root.is_absolute():
        root = Path.cwd() / root
    sessions = discover_session_dirs(root=root)
    if not sessions:
        raise SystemExit(f"error: no sessions found under {root}")
    return sessions[0]


def handle_list(args: argparse.Namespace) -> int:
    from ..application.session_recorder import discover_session_dirs, load_session_document

    root = Path(args.root).expanduser()
    if not root.is_absolute():
        root = Path.cwd() / root
    sessions = discover_session_dirs(root=root)
    rows: list[dict[str, Any]] = []
    for path in sessions:
        doc = load_session_document(path)
        rows.append(
            {
                "path": str(path),
                "session_id": doc.session_id,
                "updated_at": doc.updated_at,
                "steps": doc.summary.get("total_steps", len(doc.steps)),
                "ok_steps": doc.summary.get("ok_steps", 0),
            }
        )
    print_json({"root": str(root), "count": len(rows), "sessions": rows})
    return 0


def handle_show(args: argparse.Namespace) -> int:
    from ..application.session_recorder import load_session_document, render_readme

    session_dir = _resolve_session_dir(args)
    if args.format == "readme":
        readme = session_dir / "README.md"
        text = readme.read_text(encoding="utf-8") if readme.is_file() else render_readme(load_session_document(session_dir))
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")
        return 0
    doc = load_session_document(session_dir)
    if args.format == "summary":
        summary_payload: dict[str, Any] = {
            "session_id": doc.session_id,
            "summary": doc.summary,
            "maps": doc.maps,
        }
        projections_dir = session_dir / "projections"
        for name in ("backend_scores.json", "control_state.json", "map_health.json"):
            path = projections_dir / name
            if path.is_file():
                summary_payload[name.removesuffix(".json")] = json.loads(path.read_text(encoding="utf-8"))
        index_path = session_dir / "index.jsonl"
        if index_path.is_file():
            summary_payload["event_count"] = sum(1 for line in index_path.read_text(encoding="utf-8").splitlines() if line.strip())
        print_json(summary_payload)
        return 0
    print_json(doc.to_dict())
    return 0


def handle_export(args: argparse.Namespace) -> int:
    from ..application.session_recorder import export_session_zip

    session_dir = Path(args.session_dir).expanduser()
    if not session_dir.is_absolute():
        session_dir = Path.cwd() / session_dir
    if not (session_dir / "session.json").is_file():
        print(f"error: not a session directory: {session_dir}", file=sys.stderr)
        return 1
    output = export_session_zip(session_dir, Path(args.output))
    print_json({"ok": True, "session_dir": str(session_dir), "zip": str(output.resolve())})
    return 0


def handle_reprocess(args: argparse.Namespace) -> int:
    from ..application.session_recorder import reprocess_session_diagnostics

    session_dir = _resolve_session_dir(args)
    try:
        report = reprocess_session_diagnostics(session_dir)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print_json({"ok": True, **report})
    return 0
