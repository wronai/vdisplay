from __future__ import annotations

import argparse

from ..application.config_options import get_runtime_options


def add_display_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--display", default=None, help="X11 display (default: auto-resolve host :0)")


def add_all_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--all",
        dest="include_all",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include all entries (default: true)",
    )


def add_window_filter_args(parser: argparse.ArgumentParser) -> None:
    add_all_arg(parser)
    parser.add_argument(
        "--apps-only",
        action="store_true",
        help="Application windows only (same as --no-all)",
    )
    parser.add_argument("--min-width", type=int, default=0)
    parser.add_argument("--min-height", type=int, default=0)
    parser.add_argument("--class", dest="wm_class", help="Filter by WM_CLASS")
    parser.add_argument("--pid", type=int, help="Filter by process ID")
    parser.add_argument("--app", help="Filter by app_label / process_name")
    parser.add_argument(
        "--correlate",
        action="store_true",
        help="Merge X11 + GNOME Shell + AT-SPI + ps into surfaces (Wayland-native apps)",
    )
    parser.add_argument(
        "--app-surfaces",
        action="store_true",
        help="With --correlate: emit only app_surfaces (one row per IDE family, no browser helpers)",
    )


def include_all_from_args(args: argparse.Namespace) -> bool:
    return bool(getattr(args, "include_all", True) and not getattr(args, "apps_only", False))


def _cli_options():
    return get_runtime_options()


def add_control_selector_args(parser: argparse.ArgumentParser) -> None:
    """Selector/session flags shared by control and diagnose control."""
    opts = _cli_options()
    parser.add_argument("--selector", help='e.g. #submit, button[name="Save"], line[3]')
    parser.add_argument("--name", help="Exact control name")
    parser.add_argument("--role", help="Control role (button, input, ...)")
    parser.add_argument("--app", help="Application label or window title")
    parser.add_argument("--window-title", help="Window/frame title filter")
    parser.add_argument("--window-id")
    parser.add_argument("--index", type=int, default=0)
    parser.add_argument(
        "--backend",
        default="auto",
        choices=opts.control_backends,
    )
    parser.add_argument("--environment", choices=opts.control_environments)
    parser.add_argument("--text", help="Exact visible text match")
    parser.add_argument("--text-contains", help="Substring text match")
    parser.add_argument("--terminal-line", type=int, help="1-based terminal line number")
    parser.add_argument("--terminal-col", type=int, help="1-based terminal column number")
    parser.add_argument("--session-id", help="Terminal or browser session id")
    parser.add_argument("--dom-css", help="CSS selector for browser/DOM control")
    parser.add_argument("--dom-xpath", help="XPath selector for browser/DOM control")
    parser.add_argument("--vision-anchor", help="Vision OCR anchor text")
    parser.add_argument("--vision-template", help="Vision template PNG path or base64")
    parser.add_argument(
        "--vision-anchor-rel",
        choices=_cli_options().vision_anchor_relations,
        help="Spatial relation from vision anchor to target",
    )
    parser.add_argument("--vision-target", help="Vision target text relative to anchor")
    parser.add_argument(
        "--vision-min-confidence",
        type=float,
        default=None,
        help="Vision match threshold 0.0–1.0 (OCR + template); filters weak matches before --index",
    )


def add_map_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--map", dest="map_path", help="GUI Map Pack JSON (map.json)")
    parser.add_argument("--scope", dest="map_scope", help="Map region id to limit capture/OCR")
    parser.add_argument("--target", dest="map_target", help="Map element id for click/set-value")


def add_preview_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Render vision match overlay PNG (requires --backend vision or vision selector)",
    )
    parser.add_argument(
        "--preview-output",
        "-o",
        dest="preview_output",
        help="Write overlay PNG to path (e.g. preview.png)",
    )
    parser.add_argument(
        "--preview-debug",
        action="store_true",
        help="Include rejected matches and selector debug metadata in preview JSON",
    )


def control_selector_kwargs_from_args(args: argparse.Namespace) -> dict:
    return {
        "selector": getattr(args, "selector", None),
        "name": getattr(args, "name", None),
        "role": getattr(args, "role", None),
        "app": getattr(args, "app", None),
        "window_title": getattr(args, "window_title", None),
        "window_id": getattr(args, "window_id", None),
        "index": getattr(args, "index", 0),
        "backend": getattr(args, "backend", "auto"),
        "environment": getattr(args, "environment", None),
        "text": getattr(args, "text", None),
        "text_contains": getattr(args, "text_contains", None),
        "terminal_line": getattr(args, "terminal_line", None),
        "terminal_col": getattr(args, "terminal_col", None),
        "session_id": getattr(args, "session_id", None),
        "dom_css": getattr(args, "dom_css", None),
        "dom_xpath": getattr(args, "dom_xpath", None),
        "vision_anchor": getattr(args, "vision_anchor", None),
        "vision_template": getattr(args, "vision_template", None),
        "vision_anchor_rel": getattr(args, "vision_anchor_rel", None),
        "vision_target": getattr(args, "vision_target", None),
        "vision_min_confidence": getattr(args, "vision_min_confidence", None),
        "map_path": getattr(args, "map_path", None),
        "map_scope": getattr(args, "map_scope", None),
        "map_target": getattr(args, "map_target", None),
    }


def control_selector_kwargs_for_service(args: argparse.Namespace) -> dict:
    """Selector kwargs without ``backend`` — pass ``backend=args.backend`` explicitly."""
    payload = control_selector_kwargs_from_args(args)
    payload.pop("backend", None)
    return payload
