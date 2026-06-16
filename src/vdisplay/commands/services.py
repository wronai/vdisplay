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
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path
from urllib.parse import urlparse

from ..exceptions import VDisplayError
from .electron_share import (
    _agent_get,
    _manager_get,
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
    explicit = str(getattr(args, "agent_url", None) or "").strip()
    if explicit:
        return explicit.rstrip("/")
    try:
        manager = _manager_get(args, "/status")
    except Exception:
        manager = {}
    if isinstance(manager, dict):
        bridge = manager.get("browser_bridge") if isinstance(manager.get("browser_bridge"), dict) else {}
        agent_env = manager.get("agent_env") if isinstance(manager.get("agent_env"), dict) else {}
        for value in (bridge.get("agent_url"), agent_env.get("agent_url")):
            text = str(value or "").strip()
            if text:
                return text.rstrip("/")
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


def _stop_portal_screencast(agent_url: str, *, ignore_browser_bridge: bool = False) -> dict | None:
    try:
        status = _agent_get(agent_url, "/session/screencast/status", timeout_s=3.0)
    except VDisplayError:
        return None
    data = status.get("data") or status
    bridge = data.get("browser_bridge") if isinstance(data.get("browser_bridge"), dict) else {}
    if not ignore_browser_bridge and data.get("keeper_mode") == "browser_bridge" and bridge.get("registered"):
        return {
            "ok": True,
            "skipped": True,
            "reason": "browser_bridge_active",
            "hint": "Electron browser bridge owns capture — portal keeper left untouched",
        }
    if not data.get("active"):
        return {"ok": True, "skipped": True, "reason": "no active screencast"}
    try:
        from ..client import AgentClient

        return AgentClient(agent_url, timeout=10.0).stop_screencast()
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _clear_browser_bridge(agent_url: str) -> dict | None:
    try:
        request = urllib.request.Request(
            f"{agent_url.rstrip('/')}/session/browser-bridge/clear",
            data=b"{}",
            headers={"content-type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=3.0) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
    data = payload.get("data") if isinstance(payload, dict) and isinstance(payload.get("data"), dict) else payload
    return dict(data or {})


def _ensure_services_agent_url(args: argparse.Namespace) -> str:
    """Align prepare/status probes with the agent Electron is actually using."""
    agent_url = _services_agent_url(args)
    args.agent_url = agent_url
    os.environ["VDISPLAY_AGENT_URL"] = agent_url
    os.environ["VDISPLAY_ELECTRON_AGENT_URL"] = agent_url
    return agent_url


def _capture_ready_from_prepare(args: argparse.Namespace) -> tuple[bool, dict]:
    _ensure_services_agent_url(args)
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


def _trigger_electron_share_stop(args: argparse.Namespace) -> dict:
    share_url = f"http://{args.host}:{args.port}"
    request = urllib.request.Request(
        f"{share_url}/share/stop",
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
    return {"ok": False, "error": "invalid share/stop response", "share_url": share_url}


def _compact_share_stop(payload: dict | None) -> dict | None:
    if not isinstance(payload, dict):
        return payload
    renderer = payload.get("renderer_status") if isinstance(payload.get("renderer_status"), dict) else {}
    compact: dict = {
        "ok": bool(payload.get("ok")),
        "share_url": payload.get("share_url") or payload.get("url"),
        "sharing": bool(payload.get("sharing") or renderer.get("sharing")),
    }
    for key in ("capture_stop", "activeSourceId", "activeSourceName", "sharedDisplayId", "sharedDisplayLabel"):
        value = payload.get(key)
        if value not in (None, "", {}, []):
            compact[key] = value
    renderer_compact = {
        key: renderer.get(key)
        for key in ("sharing", "error", "hint", "sharedDisplayId", "sharedDisplayLabel")
        if renderer.get(key) not in (None, "", {}, [])
    }
    if renderer_compact:
        compact["renderer_status"] = renderer_compact
    return compact


def _trigger_electron_main_capture(
    args: argparse.Namespace,
    *,
    force: bool = False,
    display_id: str | None = None,
    timeout_s: float | None = None,
) -> dict:
    share_url = f"http://{args.host}:{args.port}"
    query: list[str] = []
    if force:
        query.append("force=1")
    if display_id:
        query.append(f"displayId={urllib.parse.quote(str(display_id))}")
    url = f"{share_url}/share/main-capture"
    if query:
        url = f"{url}?{'&'.join(query)}"
    request = urllib.request.Request(
        url,
        data=b"{}",
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            request,
            timeout=float(timeout_s if timeout_s is not None else getattr(args, "capture_request_timeout_s", 20.0)),
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {"ok": False, "error": str(exc), "share_url": share_url}
    if isinstance(payload, dict):
        payload.setdefault("share_url", share_url)
        return payload
    return {"ok": False, "error": "invalid share/main-capture response", "share_url": share_url}


def _shared_display_id_from_manager(manager: dict | None) -> str:
    if not isinstance(manager, dict):
        return ""
    renderer = manager.get("renderer_status") if isinstance(manager.get("renderer_status"), dict) else {}
    for key in ("sharedDisplayId",):
        value = str(manager.get(key) or renderer.get(key) or "").strip()
        if value:
            return value
    return ""


def _frame_stale(last_frame_age_ms: int | float | None, *, ttl_ms: float = 5000.0) -> bool:
    if last_frame_age_ms is None:
        return True
    try:
        return float(last_frame_age_ms) > ttl_ms
    except (TypeError, ValueError):
        return True


def _recover_electron_capture(args: argparse.Namespace, manager: dict | None = None) -> dict:
    if not _port_open(str(args.host), int(args.port)):
        return {"ok": False, "error": f"Electron manager not reachable on {args.host}:{args.port}"}
    display_id = _shared_display_id_from_manager(manager)
    share_start = _trigger_electron_share_start(args)
    main_capture = _trigger_electron_main_capture(
        args,
        force=True,
        display_id=display_id or None,
        timeout_s=20.0,
    )
    # Do not call /share/stop when capture is already active — that kills a healthy
    # GNOME/PipeWire session and forces a new permission dialog. force=1 on
    # /share/main-capture refreshes the main-process capture loop instead.
    if (main_capture.get("already_active") or main_capture.get("skipped")) and main_capture.get("ok"):
        return {
            "ok": True,
            "share_start": share_start,
            "share_stop": None,
            "main_capture": main_capture,
            "main_capture_retry": None,
            "display_id": display_id or None,
        }
    return {
        "ok": bool(main_capture.get("ok")),
        "share_start": share_start,
        "share_stop": None,
        "main_capture": main_capture,
        "main_capture_retry": None,
        "display_id": display_id or None,
    }


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

    os.environ["VDISPLAY_AGENT_URL"] = agent_url
    os.environ["VDISPLAY_ELECTRON_AGENT_URL"] = agent_url
    os.environ["VDISPLAY_ELECTRON_REMOTE_START_CAPTURE"] = "0"
    os.environ["VDISPLAY_ELECTRON_ALLOW_REMOTE_START_CAPTURE"] = "0"
    os.environ["VDISPLAY_ELECTRON_AUTO_RESUME_CAPTURE"] = "0"
    os.environ["VDISPLAY_ELECTRON_ALLOW_AUTO_RESUME_CAPTURE"] = "0"
    os.environ["VDISPLAY_ELECTRON_UNSAFE_AUTO_CAPTURE"] = "0"
    # Keep the Electron manager passive even when services performs a recovery.
    # Recovery uses /share/main-capture?force=1 as a one-shot local CLI action;
    # leaving AUTO_RESUME/REMOTE/UNSAFE enabled inside Electron causes repeated
    # desktopCapturer/GNOME permission prompts after startup or stale frames.

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

    bridge_clear = _clear_browser_bridge(agent_url)
    if bridge_clear:
        payload["browser_bridge_clear"] = bridge_clear
    screencast_stop = _stop_portal_screencast(agent_url, ignore_browser_bridge=True)
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
        manager = prepare.get("manager") if isinstance(prepare.get("manager"), dict) else None
        bridge = prepare.get("browser_bridge") if isinstance(prepare.get("browser_bridge"), dict) else {}
        monitor = (bridge.get("monitors") or {}).get(source) if isinstance(bridge.get("monitors"), dict) else {}
        last_age = monitor.get("age_ms") if isinstance(monitor, dict) else None
        if getattr(args, "auto_recover_capture", False) and _port_open(str(args.host), int(args.port)) and (
            not manager or not manager.get("sharing") or _frame_stale(last_age)
        ):
            payload["capture_recover"] = _recover_electron_capture(args, manager)
            ready_after, last_prepare = _capture_ready_from_prepare(args)
            payload["prepare"] = last_prepare
            payload["capture_ready"] = ready_after
            payload["sharing"] = bool((last_prepare.get("manager") or {}).get("sharing"))
            if ready_after:
                payload["ok"] = True
                payload["hint"] = (
                    "Capture ready — run: koru autopilot prepare-vdisplay "
                    f"--ide {_resolve_target(args)}"
                )
                return payload

    if not payload["capture_ready"]:
        _maybe_open_browser_bridge(args, browser_bridge_url, payload)

    if payload["capture_ready"]:
        payload["ok"] = True
        payload["hint"] = (
            "Capture ready — run: koru autopilot prepare-vdisplay "
            f"--ide {_resolve_target(args)}"
        )
        return payload

    if not getattr(args, "wait_capture", True):
        manager = prepare.get("manager") if isinstance(prepare.get("manager"), dict) else {}
        if manager.get("ok"):
            payload["ok"] = True
            payload["awaiting_capture"] = True
            payload["hint"] = (
                "Electron manager ready; capture is waiting for user action — "
                f"click Share monitor once in Electron for {source}. "
                f"Optional Chrome/Chromium fallback only if Electron fails: {browser_bridge_url}"
            )
            return payload

    if getattr(args, "wait_capture", True):
        deadline = time.monotonic() + float(getattr(args, "capture_timeout_s", 120.0))
        last_prepare = prepare
        last_recover_at = 0.0
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
            bridge = last_prepare.get("browser_bridge") if isinstance(last_prepare.get("browser_bridge"), dict) else {}
            monitor = (bridge.get("monitors") or {}).get(source) if isinstance(bridge.get("monitors"), dict) else {}
            last_age = monitor.get("age_ms") if isinstance(monitor, dict) else None
            now = time.monotonic()
            if (
                getattr(args, "auto_recover_capture", False)
                and
                _port_open(str(args.host), int(args.port))
                and (now - last_recover_at) >= 30.0
                and (not manager.get("sharing") or _frame_stale(last_age))
            ):
                payload["capture_recover"] = _recover_electron_capture(args, manager)
                last_recover_at = now
            if manager.get("sharing") and not ready:
                print(
                    "Electron is sharing locally but agent capture_ready is false — "
                    "check VDISPLAY_AGENT_URL matches the running agent",
                    file=sys.stderr,
                )
            elif _port_open(str(args.host), int(args.port)):
                print(
                    "Waiting for capture_ready: click Share monitor once in Electron, "
                    f"select whole monitor {source}. Optional browser fallback: {browser_bridge_url}",
                    file=sys.stderr,
                )
            time.sleep(2.0)
        payload["prepare"] = last_prepare
        payload["capture_ready"] = bool(last_prepare.get("capture_ready"))
        payload["timeout"] = True

    payload["hint"] = (
        "Capture not ready — keep Electron focused, grant Screen Recording for vdisplay share/Electron, "
        f"then: vdisplay services resume --source {source} --port {args.port} "
        f"or click Share monitor in the Electron window"
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
        "# vdisplay services up: agent + Electron manager (browser fallback optional)",
        file=sys.stderr,
    )
    payload = build_up_payload(args)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload.get("ok") else 1


def build_resume_payload(args: argparse.Namespace) -> dict:
    agent_url = _ensure_services_agent_url(args)
    source = _resolve_source(args)
    prepare = build_prepare_payload(args)
    manager = prepare.get("manager") if isinstance(prepare.get("manager"), dict) else None
    payload: dict = {
        "ok": False,
        "agent_url": agent_url,
        "source": source,
        "share_url": f"http://{args.host}:{args.port}",
        "capture_ready": bool(prepare.get("capture_ready")),
        "sharing": bool((manager or {}).get("sharing")),
        "prepare_before": prepare,
    }
    if prepare.get("capture_ready"):
        payload["ok"] = True
        payload["hint"] = "Capture already ready — no resume needed"
        return payload
    payload["capture_recover"] = _recover_electron_capture(args, manager)
    ready, last_prepare = _capture_ready_from_prepare(args)
    payload["prepare"] = last_prepare
    payload["capture_ready"] = ready
    payload["sharing"] = bool((last_prepare.get("manager") or {}).get("sharing"))
    if ready:
        payload["ok"] = True
        payload["hint"] = (
            "Capture resumed — run: koru autopilot prepare-vdisplay "
            f"--ide {_resolve_target(args)}"
        )
        return payload
    main_capture = (payload.get("capture_recover") or {}).get("main_capture") or {}
    payload["error"] = str(main_capture.get("error") or "capture still not ready after resume")
    payload["hint"] = (
        "Keep the Electron window focused, enable Screen Recording for vdisplay share/Electron, "
        "then click Grant via GNOME or Share monitor once"
    )
    return payload


def handle_resume(args: argparse.Namespace) -> int:
    payload = build_resume_payload(args)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload.get("ok") else 1


def handle_status(args: argparse.Namespace) -> int:
    from .electron_share import handle_health

    return handle_health(args)


def handle_down(args: argparse.Namespace) -> int:
    agent_url = _services_agent_url(args)
    payload: dict = {"ok": True, "agent_url": agent_url}
    if _port_open(str(args.host), int(args.port)):
        payload["share_stop"] = _compact_share_stop(_trigger_electron_share_stop(args))
    try:
        with redirect_stdout(io.StringIO()):
            payload["electron_stop"] = {"exit_code": electron_stop(args)}
    except VDisplayError as exc:
        payload["electron_stop"] = {"ok": False, "error": str(exc)}
    payload["browser_bridge_clear"] = _clear_browser_bridge(agent_url)
    payload["screencast_stop"] = _stop_portal_screencast(agent_url, ignore_browser_bridge=True)
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
        "--system-picker",
        action="store_true",
        help="Use GNOME/Chromium system picker (opt-in; default shares whole monitor via grid)",
    )
    up.add_argument(
        "--no-system-picker",
        action="store_true",
        help="Explicitly disable system picker (default since monitor-first flow)",
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
    up.add_argument(
        "--auto-recover-capture",
        action="store_true",
        help="Run one-shot /share/main-capture recovery while waiting; does not enable background auto-resume",
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

    resume = action.add_parser(
        "resume",
        help="Re-trigger Electron monitor capture when frames are stale (no full restart)",
    )
    resume.add_argument("--host", default="127.0.0.1")
    resume.add_argument("--port", type=int, default=8799)
    resume.add_argument("--timeout-s", type=float, default=3.0)
    resume.add_argument("--agent-url")
    resume.add_argument("--source", default="HDMI-1")
    resume.add_argument("--instance", default="jetbrains")
    resume.add_argument("--target", default="jetbrains")
    resume.set_defaults(func=handle_resume)

    down = action.add_parser(
        "down",
        help="Stop Electron share and portal screencast (agent keeps running)",
    )
    down.add_argument("--host", default="127.0.0.1")
    down.add_argument("--port", type=int, default=8799)
    down.add_argument("--timeout-s", type=float, default=3.0)
    down.add_argument("--agent-url")
    down.set_defaults(func=handle_down)
