"""Orchestrate vdisplay-agent + Electron share for Koru photo-VQL workflows."""

from __future__ import annotations

import argparse
import io
import json
from contextlib import redirect_stdout
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path
from urllib.parse import urlparse

from ..exceptions import VDisplayError
from .electron_share import (
    _agent_get,
    _port_open,
    _resolve_agent_url,
    _resolve_instance,
    _resolve_source,
    _resolve_target,
    build_prepare_payload,
    handle_stop as electron_stop,
    handle_up as electron_up,
)


def _state_dir() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(base) / "vdisplay" / "services"


def _agent_host_port(agent_url: str) -> tuple[str, int]:
    parsed = urlparse(agent_url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or int(os.environ.get("VDISPLAY_AGENT_PORT") or "8766")
    return host, port


def _services_agent_url(args: argparse.Namespace) -> str:
    return (_resolve_agent_url(args) or "http://127.0.0.1:8766").rstrip("/")


def _browser_bridge_url(agent_url: str, source: str) -> str:
    return f"{agent_url.rstrip('/')}/api/web/browser-bridge?source={source}"


def _maybe_open_browser_bridge(args: argparse.Namespace, url: str, payload: dict) -> None:
    if not getattr(args, "open_browser_bridge", False):
        return
    try:
        opened = webbrowser.open(url)
    except Exception as exc:
        payload["browser_bridge_open"] = {"ok": False, "url": url, "error": str(exc)}
    else:
        payload["browser_bridge_open"] = {"ok": bool(opened), "url": url}


def _agent_alive(agent_url: str, *, timeout_s: float = 2.0) -> bool:
    try:
        payload = _agent_get(agent_url, "/health", timeout_s=timeout_s)
    except VDisplayError:
        return False
    if payload.get("ok") is True:
        return True
    data = payload.get("data")
    return isinstance(data, dict) and str(data.get("status") or "").lower() == "ok"


def _wait_agent(agent_url: str, *, timeout_s: float) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if _agent_alive(agent_url):
            return True
        time.sleep(0.35)
    return _agent_alive(agent_url)


def _start_agent_background(host: str, port: int) -> tuple[subprocess.Popen, Path]:
    agent_bin = shutil.which("vdisplay-agent")
    if not agent_bin:
        raise VDisplayError(
            "vdisplay-agent not found in PATH — activate the vdisplay .venv "
            "(pip install -e packages/vdisplay-agent[serve])"
        )
    log_path = _state_dir() / f"agent-{port}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    agent_url = f"http://{host}:{port}"
    env["VDISPLAY_AGENT_URL"] = agent_url
    env["VDISPLAY_AGENT_PORT"] = str(port)
    env["VDISPLAY_ELECTRON_AGENT_URL"] = agent_url
    with log_path.open("ab") as log_file:
        proc = subprocess.Popen(
            [agent_bin, "serve", "--host", host, "--port", str(port)],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            env=env,
        )
    return proc, log_path


def _stop_portal_screencast(agent_url: str) -> dict | None:
    try:
        status = _agent_get(agent_url, "/session/screencast/status", timeout_s=3.0)
    except VDisplayError:
        return None
    data = status.get("data") or status
    if not data.get("active"):
        return {"ok": True, "skipped": True, "reason": "no active screencast"}
    try:
        from ..client import AgentClient

        return AgentClient(agent_url, timeout=10.0).stop_screencast()
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _capture_ready_from_prepare(args: argparse.Namespace) -> tuple[bool, dict]:
    payload = build_prepare_payload(args)
    return bool(payload.get("capture_ready")), payload


def _print_env_exports(agent_url: str, share_url: str, source: str) -> None:
    print(f"export VDISPLAY_AGENT_URL={agent_url}", file=sys.stderr)
    print(f"export VDISPLAY_ELECTRON_AGENT_URL={agent_url}", file=sys.stderr)
    print(f"export VDISPLAY_ELECTRON_SHARE_URL={share_url}", file=sys.stderr)
    print(f"# bridge source: {source}", file=sys.stderr)


def _trigger_electron_share_start(args: argparse.Namespace) -> dict:
    share_url = f"http://{args.host}:{args.port}"
    request = urllib.request.Request(
        f"{share_url}/share/start",
        data=b"{}",
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=float(getattr(args, "timeout_s", 3.0))) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {"ok": False, "error": str(exc), "share_url": share_url}
    if isinstance(payload, dict):
        payload.setdefault("share_url", share_url)
        return payload
    return {"ok": False, "error": "invalid share/start response", "share_url": share_url}


def _trigger_electron_main_capture(args: argparse.Namespace) -> dict:
    share_url = f"http://{args.host}:{args.port}"
    request = urllib.request.Request(
        f"{share_url}/share/main-capture",
        data=b"{}",
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=float(getattr(args, "timeout_s", 8.0))) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {"ok": False, "error": str(exc), "share_url": share_url}
    if isinstance(payload, dict):
        payload.setdefault("share_url", share_url)
        return payload
    return {"ok": False, "error": "invalid share/main-capture response", "share_url": share_url}


def build_up_payload(args: argparse.Namespace) -> dict:
    agent_url = _services_agent_url(args)
    host, port = _agent_host_port(agent_url)
    share_url = f"http://{args.host}:{args.port}"
    source = _resolve_source(args)
    browser_bridge_url = _browser_bridge_url(agent_url, source)
    payload: dict = {
        "ok": False,
        "agent_url": agent_url,
        "share_url": share_url,
        "browser_bridge_url": browser_bridge_url,
        "source": source,
        "instance": _resolve_instance(args),
        "target": _resolve_target(args),
        "steps": [],
    }

    os.environ.setdefault("VDISPLAY_AGENT_URL", agent_url)
    os.environ.setdefault("VDISPLAY_ELECTRON_AGENT_URL", agent_url)

    agent_started = False
    agent_proc: subprocess.Popen | None = None
    agent_log: Path | None = None
    if not _agent_alive(agent_url):
        if not getattr(args, "start_agent", True):
            payload["error"] = f"agent not reachable at {agent_url}"
            payload["hint"] = f"vdisplay-agent serve --port {port}"
            return payload
        agent_proc, agent_log = _start_agent_background(host, port)
        agent_started = True
        payload["agent_started"] = True
        payload["agent_pid"] = agent_proc.pid
        payload["agent_log"] = str(agent_log)
        if not _wait_agent(agent_url, timeout_s=float(getattr(args, "agent_startup_timeout_s", 15.0))):
            tail = ""
            if agent_log and agent_log.is_file():
                tail = agent_log.read_text(encoding="utf-8", errors="replace")[-800:]
            payload["error"] = f"agent did not become ready at {agent_url}"
            payload["agent_log_tail"] = tail
            return payload
    else:
        payload["agent_started"] = False
        payload["agent_already_running"] = True

    screencast_stop = _stop_portal_screencast(agent_url)
    if screencast_stop:
        payload["screencast_stop"] = screencast_stop

    electron_result: dict | None = None
    try:
        with redirect_stdout(io.StringIO()):
            code = electron_up(args)
        electron_result = {"exit_code": code}
    except VDisplayError as exc:
        payload["electron_error"] = str(exc)
        payload["hint"] = (
            "Electron failed to start — run: vdisplay electron-share start "
            f"--instance {payload['instance']} --source {source} --port {args.port}"
        )
        return payload

    prepare = build_prepare_payload(args)
    payload["electron"] = electron_result
    payload["prepare"] = prepare
    payload["capture_ready"] = bool(prepare.get("capture_ready"))
    payload["sharing"] = bool((prepare.get("manager") or {}).get("sharing"))

    if not payload["capture_ready"]:
        _maybe_open_browser_bridge(args, browser_bridge_url, payload)

    if payload["capture_ready"]:
        payload["ok"] = True
        payload["hint"] = (
            "Capture ready — run: koru autopilot prepare-vdisplay "
            f"--ide {_resolve_target(args)}"
        )
        return payload

    if getattr(args, "wait_capture", True):
        deadline = time.monotonic() + float(getattr(args, "capture_timeout_s", 120.0))
        last_prepare = prepare
        while time.monotonic() < deadline:
            ready, last_prepare = _capture_ready_from_prepare(args)
            payload["prepare"] = last_prepare
            payload["capture_ready"] = ready
            payload["sharing"] = bool((last_prepare.get("manager") or {}).get("sharing"))
            if ready:
                payload["ok"] = True
                payload["hint"] = (
                    "Capture ready — run: koru autopilot prepare-vdisplay "
                    f"--ide {_resolve_target(args)}"
                )
                return payload
            manager = last_prepare.get("manager") or {}
            if manager.get("sharing") and not ready:
                print(
                    "Electron is sharing locally but agent capture_ready is false — "
                    "check VDISPLAY_AGENT_URL matches the running agent",
                    file=sys.stderr,
                )
            elif _port_open(str(args.host), int(args.port)):
                print(
                    "Waiting for capture_ready: open browser bridge, click Share screen, "
                    f"select {source}, keep the tab open: {browser_bridge_url}",
                    file=sys.stderr,
                )
            time.sleep(2.0)
        payload["prepare"] = last_prepare
        payload["capture_ready"] = bool(last_prepare.get("capture_ready"))
        payload["timeout"] = True

    payload["hint"] = (
        "Manual step required: open browser bridge in Chrome/Chromium, click Share screen, "
        f"select {source}, keep the tab open, "
        f"then: vdisplay electron-share health --port {args.port} --source {source} && "
        f"koru autopilot prepare-vdisplay --ide {_resolve_target(args)}"
    )
    if not payload.get("ok"):
        payload.setdefault(
            "error",
            "capture not ready — browser bridge has no fresh frames",
        )
    return payload


def handle_up(args: argparse.Namespace) -> int:
    agent_url = _services_agent_url(args)
    share_url = f"http://{args.host}:{args.port}"
    _print_env_exports(agent_url, share_url, _resolve_source(args))
    print(
        "# vdisplay services up: agent + Electron manager + browser bridge",
        file=sys.stderr,
    )
    payload = build_up_payload(args)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload.get("ok") else 1


def handle_status(args: argparse.Namespace) -> int:
    from .electron_share import handle_health

    return handle_health(args)


def handle_down(args: argparse.Namespace) -> int:
    agent_url = _services_agent_url(args)
    payload: dict = {"ok": True, "agent_url": agent_url}
    payload["screencast_stop"] = _stop_portal_screencast(agent_url)
    try:
        payload["electron_stop"] = {"exit_code": electron_stop(args)}
    except VDisplayError as exc:
        payload["electron_stop"] = {"ok": False, "error": str(exc)}
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser(
        "services",
        help="Start agent + Electron share for Koru photo-VQL (orchestrated stack)",
    )
    action = parser.add_subparsers(dest="services_action", required=True)

    up = action.add_parser(
        "up",
        help="Start vdisplay-agent (if down), stop portal screencast, start Electron, wait for capture",
    )
    up.add_argument("--host", default="127.0.0.1", help="Electron HTTP host")
    up.add_argument("--port", type=int, default=8799, help="Electron HTTP port")
    up.add_argument("--timeout-s", type=float, default=3.0, help="HTTP timeout for checks")
    up.add_argument("--instance", default="jetbrains", help="Electron instance label")
    up.add_argument("--target", default="jetbrains", help="Target app label")
    up.add_argument("--source", default="HDMI-1", help="Bridge source / monitor name")
    up.add_argument("--agent-url", help="vdisplay-agent URL (defaults to VDISPLAY_AGENT_URL)")
    up.add_argument(
        "--no-agent-bridge",
        action="store_true",
        help="Disable Electron push bridge to vdisplay-agent",
    )
    up.add_argument("--mode", choices=("compact", "full"), default="full")
    up.add_argument("--no-always-on-top", action="store_true")
    up.add_argument(
        "--no-system-picker",
        action="store_true",
        help="Use Electron source handler instead of Chromium/system picker where available",
    )
    up.add_argument(
        "--close-quits",
        action="store_true",
        help="Make window close quit instead of hiding to tray",
    )
    up.add_argument("--ozone-platform", choices=("wayland", "x11"))
    up.add_argument(
        "--startup-timeout-s",
        type=float,
        default=25.0,
        help="Seconds to wait for Electron HTTP after start",
    )
    up.add_argument(
        "--agent-startup-timeout-s",
        type=float,
        default=15.0,
        help="Seconds to wait for vdisplay-agent /health after background start",
    )
    up.add_argument(
        "--capture-timeout-s",
        type=float,
        default=120.0,
        help="Seconds to wait for capture_ready after Electron is up",
    )
    up.add_argument(
        "--no-wait-capture",
        dest="wait_capture",
        action="store_false",
        help="Do not poll for capture_ready (exit after Electron starts)",
    )
    up.add_argument(
        "--no-start-agent",
        dest="start_agent",
        action="store_false",
        help="Fail if vdisplay-agent is not already running",
    )
    up.add_argument(
        "--open-browser-bridge",
        action="store_true",
        help="Open the Chrome/Chromium browser bridge URL after services start",
    )
    up.add_argument("--install", action="store_true", help="Run npm install before Electron start")
    up.set_defaults(func=handle_up, wait_capture=True, start_agent=True)

    status = action.add_parser("status", help="Combined Electron + agent health")
    status.add_argument("--host", default="127.0.0.1")
    status.add_argument("--port", type=int, default=8799)
    status.add_argument("--timeout-s", type=float, default=3.0)
    status.add_argument("--agent-url")
    status.add_argument("--source", default="HDMI-1")
    status.set_defaults(func=handle_status)

    down = action.add_parser(
        "down",
        help="Stop Electron share and portal screencast (agent keeps running)",
    )
    down.add_argument("--host", default="127.0.0.1")
    down.add_argument("--port", type=int, default=8799)
    down.add_argument("--timeout-s", type=float, default=3.0)
    down.add_argument("--agent-url")
    down.set_defaults(func=handle_down)
