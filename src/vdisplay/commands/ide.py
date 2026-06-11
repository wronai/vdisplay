from __future__ import annotations

import argparse
import time

from ..application.commands import CommandRequest, CommandResult, CommandVerb
from ..application.errors import error_from_exception
from ..application.session_context import enrich_command_request, ensure_audit_session_dir
from ..application.session_recorder import record_execution, session_recording_enabled
from ..desktop_apps import list_desktop_apps
from ..exceptions import VDisplayError
from ..ide_prompt import send_ide_prompt
from .common import add_display_arg, add_map_args
from ..application.config_options import get_runtime_options
from .io import print_json


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("ide", help="IDE prompt helper (launch, focus, type)")
    ide_sub = parser.add_subparsers(dest="action", required=True)

    listing = ide_sub.add_parser("list", help="List IDE apps with control hints")
    listing.set_defaults(func=handle)

    prompt = ide_sub.add_parser("prompt", help="Focus IDE and type a chat prompt")
    add_display_arg(prompt)
    prompt.add_argument("--ide", required=True, help="IDE/app id (pycharm, cursor, vscode, ...)")
    prompt.add_argument("--text", required=True, help="Prompt text to type")
    prompt.add_argument(
        "--backend",
        default=None,
        choices=get_runtime_options().control_backends,
        help="Control backend override (default: app profile)",
    )
    prompt.add_argument("--open", action="store_true", help="Launch IDE before typing")
    prompt.add_argument("--variant", help="Launch variant when --open is set")
    prompt.add_argument(
        "--no-wait-window",
        action="store_true",
        help="Skip waiting for app window before focus",
    )
    prompt.add_argument(
        "--wait-timeout",
        type=float,
        default=20.0,
        help="Seconds to wait for app window (default: 20)",
    )
    prompt.add_argument("--submit", action="store_true", help="Click send or submit after typing")
    prompt.add_argument("--verify", action="store_true", help="Verify set-value result")
    add_map_args(prompt)
    prompt.set_defaults(func=handle)


def handle(args: argparse.Namespace) -> int:
    if args.action == "list":
        print_json({"ides": list_desktop_apps(), "count": len(list_desktop_apps())})
        return 0
    if args.action == "prompt":
        try:
            started = time.perf_counter()
            payload = send_ide_prompt(
                app_id=args.ide,
                text=args.text,
                display=getattr(args, "display", None),
                backend=getattr(args, "backend", None),
                open_app=bool(getattr(args, "open", False)),
                launch_variant=getattr(args, "variant", None),
                wait_window=not bool(getattr(args, "no_wait_window", False)),
                wait_timeout=float(getattr(args, "wait_timeout", 20.0)),
                submit=bool(getattr(args, "submit", False)),
                map_path=getattr(args, "map_path", None),
                map_scope=getattr(args, "map_scope", None),
                map_target=getattr(args, "map_target", None),
                verify=bool(getattr(args, "verify", False)),
            )
            duration_ms = int((time.perf_counter() - started) * 1000)
            if session_recording_enabled():
                cmd = enrich_command_request(
                    CommandRequest(
                        verb=CommandVerb.CONTROL_SET_VALUE,
                        line=f"ide prompt --ide {args.ide}",
                        control_value=args.text,
                        control_app=args.ide,
                        browser_engine=getattr(args, "backend", None),
                        extra={
                            "ide_prompt": True,
                            "ide": args.ide,
                            "submit": bool(getattr(args, "submit", False)),
                            "map_path": getattr(args, "map_path", None),
                        },
                    )
                )
                ensure_audit_session_dir(cmd)
                if payload.get("ok"):
                    result = CommandResult.success(
                        action="ide_prompt",
                        data=payload,
                        command=cmd.line,
                    )
                else:
                    result = CommandResult.failure(
                        action="ide_prompt",
                        error=error_from_exception(
                            VDisplayError(str(payload.get("message") or "ide prompt failed"))
                        ),
                        data=payload,
                        command=cmd.line,
                    )
                session_dir = record_execution(cmd, result, route="local", duration_ms=duration_ms)
                if session_dir is not None:
                    payload["session_dir"] = str(session_dir)
            print_json(payload)
        except KeyError as exc:
            raise VDisplayError(str(exc)) from exc
        return 0
    raise VDisplayError(f"unknown ide action: {args.action}")
