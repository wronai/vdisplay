from __future__ import annotations

import argparse
import json
import sys
import time

from ..application.services.sampler import SamplerConfig, run_sampler, start_sampler_via_agent
from ..agent_config import resolve_agent_url
from ..client import AgentClient
from .common import add_display_arg
from .io import print_json


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser(
        "sampler",
        help="Continuous screenshot loop — local or vdisplay-agent worker",
    )
    subp = parser.add_subparsers(dest="action", required=True)

    start = subp.add_parser("start", help="Start frame sampling")
    add_display_arg(start)
    start.add_argument(
        "--mode",
        choices=["desktop", "strict", "unattended", "best-effort"],
        default="desktop",
    )
    start.add_argument("--interval", type=float, default=1.0)
    start.add_argument("--source", help="Monitor name (e.g. DP-2)")
    start.add_argument("--out-dir", default="./captures")
    start.add_argument("--max-frames", type=int, default=None)
    start.add_argument("--vd-display", default=":99")
    start.add_argument("--width", type=int, default=1280)
    start.add_argument("--height", type=int, default=720)
    start.add_argument("--format", choices=["png", "webp", "jpeg"], default="png")
    start.add_argument("--no-dedupe", action="store_true")
    start.add_argument("--progress", action="store_true")
    start.add_argument(
        "--local-only",
        action="store_true",
        help="Run blocking loop in CLI (default: background worker in agent when up)",
    )
    start.add_argument(
        "--wait",
        action="store_true",
        help="With agent worker: block until sampler stops, printing --progress lines",
    )
    start.set_defaults(func=handle)

    stop = subp.add_parser("stop", help="Stop agent background sampler")
    stop.set_defaults(func=handle)

    status = subp.add_parser("status", help="Show agent sampler status")
    status.set_defaults(func=handle)


def _config_from_args(args: argparse.Namespace) -> SamplerConfig:
    return SamplerConfig(
        interval_s=args.interval,
        mode=args.mode,
        source=args.source,
        display=args.display,
        vd_display=args.vd_display,
        output_dir=args.out_dir,
        max_frames=args.max_frames,
        dedupe=not args.no_dedupe,
        width=args.width,
        height=args.height,
        format=args.format,
    )


def handle(args: argparse.Namespace) -> int:
    url = resolve_agent_url(allow_auto=True)

    if args.action == "stop":
        if not url:
            raise SystemExit("agent not running — nothing to stop")
        print_json(AgentClient(url).sampler_stop())
        return 0

    if args.action == "status":
        if not url:
            print_json({"ok": True, "running": False, "agent_url": None})
            return 0
        print_json(AgentClient(url).sampler_status())
        return 0

    config = _config_from_args(args)
    use_agent = url is not None and not args.local_only

    if use_agent:
        result = start_sampler_via_agent(AgentClient(url), config)
        print_json(result)
        if args.wait:
            client = AgentClient(url)
            seen = 0
            while True:
                st = client.sampler_status()
                if not st.get("running"):
                    print_json(st)
                    break
                saved = int(st.get("frames_saved") or 0)
                if args.progress and saved > seen:
                    for frame in st.get("recent_frames") or []:
                        if int(frame.get("frame_index", -1)) >= seen:
                            print(json.dumps(frame), flush=True)
                    seen = saved
                time.sleep(max(0.1, config.interval_s / 2))
        return 0

    def on_frame(meta: dict) -> None:
        if args.progress:
            print(json.dumps(meta), flush=True)

    print_json(run_sampler(config, on_frame=on_frame if args.progress else None))
    return 0
