from __future__ import annotations

import argparse
import json
import sys

from .api import MirrorSession, VirtualDisplaySession, WindowRelaySession, platform_summary
from .exceptions import VDisplayError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vdisplay",
        description="Cross-platform virtual display orchestration",
    )
    sub = parser.add_subparsers(dest="kind", required=True)

    virtual = sub.add_parser("virtual", help="Private virtual display session")
    virtual_sub = virtual.add_subparsers(dest="action", required=True)

    vstart = virtual_sub.add_parser("start", help="Start Xvfb virtual display")
    vstart.add_argument("--backend", default="xvfb")
    vstart.add_argument("--width", type=int, default=1920)
    vstart.add_argument("--height", type=int, default=1080)
    vstart.add_argument("--display", default=":99")

    vlaunch = virtual_sub.add_parser("launch", help="Launch command on active virtual display")
    vlaunch.add_argument("command", nargs="+")
    vlaunch.add_argument("--backend", default="xvfb")
    vlaunch.add_argument("--width", type=int, default=1920)
    vlaunch.add_argument("--height", type=int, default=1080)
    vlaunch.add_argument("--display", default=":99")

    vshot = virtual_sub.add_parser("screenshot", help="Capture virtual display screenshot")
    vshot.add_argument("-o", "--output", required=True)
    vshot.add_argument("--backend", default="xvfb")
    vshot.add_argument("--width", type=int, default=1920)
    vshot.add_argument("--height", type=int, default=1080)
    vshot.add_argument("--display", default=":99")

    mirror = sub.add_parser("mirror", help="Mirror an existing display")
    mirror_sub = mirror.add_subparsers(dest="action", required=True)

    mstart = mirror_sub.add_parser("start", help="Start mirror session")
    mstart.add_argument("--backend", default="x11")
    mstart.add_argument("--source", default="primary")
    mstart.add_argument("--target", default=None)
    mstart.add_argument("--display", default=None)
    mstart.add_argument("-o", "--output", default=None, help="Optional screenshot path")

    relay = sub.add_parser("relay", help="Move windows within the same X11 session")
    relay_sub = relay.add_subparsers(dest="action", required=True)

    radopt = relay_sub.add_parser("adopt-window", help="Move window off-screen or to target output")
    radopt.add_argument("--title")
    radopt.add_argument("--window-id")
    radopt.add_argument("--target", default="offscreen")
    radopt.add_argument("--display", default=None)

    rrelease = relay_sub.add_parser("release-window", help="Restore adopted window")
    rrelease.add_argument("--title")
    rrelease.add_argument("--window-id")
    rrelease.add_argument("--display", default=None)

    rlist = relay_sub.add_parser("list", help="List adopted windows")
    rlist.add_argument("--display", default=None)

    sub.add_parser("info", help="Show platform capabilities")
    return parser


def _print_json(payload: dict) -> None:
    print(json.dumps(payload, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.kind == "info":
            session = VirtualDisplaySession.create(backend="xvfb")
            _print_json(
                {
                    "platform": platform_summary(),
                    "virtual_capabilities": session.capabilities(),
                    "mirror_capabilities": MirrorSession.create().capabilities(),
                    "relay_capabilities": WindowRelaySession.create().capabilities(),
                }
            )
            return 0

        if args.kind == "virtual":
            session = VirtualDisplaySession.create(
                width=args.width,
                height=args.height,
                backend=args.backend,
                display=args.display,
            )
            if args.action == "start":
                session.start()
                _print_json({"info": session.info(), "capabilities": session.capabilities()})
                return 0
            if args.action == "launch":
                session.start()
                try:
                    pid = session.launch(args.command)
                    _print_json({"pid": pid, "display": session.info()["metadata"]["display"]})
                finally:
                    session.stop()
                return 0
            if args.action == "screenshot":
                session.start()
                try:
                    path = session.save_screenshot(args.output)
                    _print_json({"saved": path, "info": session.info()})
                finally:
                    session.stop()
                return 0

        if args.kind == "mirror":
            session = MirrorSession.create(
                source=args.source,
                target=args.target,
                backend=args.backend,
                display=args.display,
            )
            if args.action == "start":
                session.start()
                try:
                    payload = {"info": session.info(), "capabilities": session.capabilities()}
                    if args.output:
                        payload["saved"] = session.save_screenshot(args.output)
                    _print_json(payload)
                finally:
                    session.stop()
                return 0

        if args.kind == "relay":
            session = WindowRelaySession.create(display=args.display)
            session.start()
            try:
                if args.action == "adopt-window":
                    wid = session.adopt_window(
                        match_title=args.title,
                        window_id=args.window_id,
                        target=args.target,
                    )
                    _print_json({"window_id": wid, "adopted": session.list_adopted()})
                    return 0
                if args.action == "release-window":
                    wid = session.release_window(
                        match_title=args.title,
                        window_id=args.window_id,
                    )
                    _print_json({"window_id": wid, "adopted": session.list_adopted()})
                    return 0
                if args.action == "list":
                    _print_json({"adopted": session.list_adopted()})
                    return 0
            finally:
                session.stop()

    except VDisplayError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    parser.error("unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
