"""Electron screen-share manager commands."""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from ..exceptions import VDisplayError


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _app_dir() -> Path:
    return _repo_root() / "packages" / "vdisplay-electron-share"


def _run(cmd: list[str], *, env: dict[str, str] | None = None) -> int:
    return subprocess.call(cmd, cwd=str(_app_dir()), env=env)


def _electron_bin() -> Path:
    candidates = (
        _app_dir() / "node_modules" / ".bin" / "electron",
        _app_dir() / "node_modules" / "electron" / "dist" / "electron",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise VDisplayError(
        "Electron binary not found — run: vdisplay electron-share install"
    )


def _electron_command(env: dict[str, str]) -> list[str]:
    return [
        str(_electron_bin()),
        "--no-sandbox",
        "--disable-gpu",
        "--disable-gpu-compositing",
        "--disable-dev-shm-usage",
        f"--gtk-version={env.get('VDISPLAY_ELECTRON_GTK_VERSION') or '3'}",
        f"--ozone-platform={env.get('VDISPLAY_ELECTRON_OZONE_PLATFORM') or 'x11'}",
        ".",
    ]


def _ensure_app_dir() -> None:
    app_dir = _app_dir()
    if not (app_dir / "package.json").is_file():
        raise VDisplayError(f"electron share app not found: {app_dir}")


def _npm_install_if_requested(args: argparse.Namespace) -> None:
    _ensure_app_dir()
    node_modules = _app_dir() / "node_modules"
    if not getattr(args, "install", False) and node_modules.is_dir():
        return
    code = _run(["npm", "install"])
    if code != 0:
        raise VDisplayError(f"npm install failed with exit code {code}")


def _resolve_agent_url(args: argparse.Namespace) -> str:
    raw = (
        getattr(args, "agent_url", None)
        or os.environ.get("VDISPLAY_ELECTRON_AGENT_URL")
        or os.environ.get("VDISPLAY_AGENT_URL")
        or ""
    )
    return str(raw).strip().rstrip("/")


def _resolve_source(args: argparse.Namespace) -> str:
    return str(
        getattr(args, "source", None)
        or os.environ.get("VDISPLAY_ELECTRON_BRIDGE_SOURCE")
        or os.environ.get("VDISPLAY_ELECTRON_SHARE_SOURCE")
        or "HDMI-1"
    ).strip() or "HDMI-1"


def _resolve_instance(args: argparse.Namespace) -> str:
    return str(
        getattr(args, "instance", None)
        or os.environ.get("VDISPLAY_ELECTRON_SHARE_INSTANCE")
        or "jetbrains"
    ).strip() or "jetbrains"


def _resolve_target(args: argparse.Namespace) -> str:
    return str(
        getattr(args, "target", None)
        or os.environ.get("VDISPLAY_ELECTRON_TARGET_LABEL")
        or "jetbrains"
    ).strip() or "jetbrains"


def _preferred_display_env_for_source(source: str) -> dict[str, str]:
    """Map a vdisplay monitor name to Electron display match hints (pixel geometry)."""
    try:
        from vdisplay.application.services.discovery import list_monitors_local
    except ImportError:
        return {}
    try:
        payload = list_monitors_local()
    except Exception:
        return {}
    monitors = payload.get("monitors") or []
    target = next(
        (
            item
            for item in monitors
            if str(item.get("name") or "").strip() == source and item.get("connected") is not False
        ),
        None,
    )
    if not target:
        return {}
    width = target.get("width_px") or target.get("width")
    height = target.get("height_px") or target.get("height")
    if not width or not height:
        return {}
    env = {
        "VDISPLAY_ELECTRON_PREFERRED_DISPLAY_X": str(int(target.get("x") or 0)),
        "VDISPLAY_ELECTRON_PREFERRED_DISPLAY_Y": str(int(target.get("y") or 0)),
        "VDISPLAY_ELECTRON_PREFERRED_DISPLAY_WIDTH": str(int(width)),
        "VDISPLAY_ELECTRON_PREFERRED_DISPLAY_HEIGHT": str(int(height)),
    }
    diagonal = target.get("diagonal_in")
    if diagonal:
        env["VDISPLAY_ELECTRON_PREFERRED_DISPLAY_DIAGONAL"] = str(diagonal)
    return env


def _bridge_heartbeat_stale(bridge_data: dict) -> bool:
    age_ms = bridge_data.get("heartbeat_age_ms")
    if age_ms is None:
        return False
    try:
        ttl_s = float(bridge_data.get("ttl_s") or 5.0)
        age = float(age_ms)
    except (TypeError, ValueError):
        return False
    return age > max(ttl_s * 2000.0, ttl_s * 1000.0 + 1000.0)


def _agent_get(agent_url: str, path: str, *, timeout_s: float = 3.0) -> dict:
    url = f"{agent_url.rstrip('/')}{path if path.startswith('/') else '/' + path}"
    try:
        with urllib.request.urlopen(url, timeout=timeout_s) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise VDisplayError(f"{url}: HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise VDisplayError(f"{url}: {exc.reason}") from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise VDisplayError(f"{url}: response is not JSON: {raw[:200]}") from exc
    return payload


def _port_open(host: str, port: int, *, timeout_s: float = 0.2) -> bool:
    try:
        with socket.create_connection((host, int(port)), timeout=timeout_s):
            return True
    except OSError:
        return False


def _stop_process_fallback(port: int | None = None) -> None:
    patterns = (
        "vdisplay-electron-share/node_modules/.bin/electron",
        "vdisplay-electron-share/node_modules/electron/dist/electron",
    )
    for pattern in patterns:
        subprocess.run(["pkill", "-f", pattern], check=False)
    if port:
        try:
            subprocess.run(
                ["fuser", "-k", f"{int(port)}/tcp"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            pass


def _wait_port_closed(host: str, port: int, *, timeout_s: float = 3.0) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if not _port_open(host, port):
            return True
        time.sleep(0.15)
    return not _port_open(host, port)


def _gnome_wayland_session() -> bool:
    wayland = bool((os.environ.get("WAYLAND_DISPLAY") or "").strip()) or (
        os.environ.get("XDG_SESSION_TYPE", "").strip().lower() == "wayland"
    )
    if not wayland:
        return False
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").strip().lower()
    return "gnome" in desktop or "ubuntu" in desktop or "unity" in desktop


def _default_ozone_platform() -> str:
    explicit = os.environ.get("VDISPLAY_ELECTRON_OZONE_PLATFORM", "").strip().lower()
    if explicit in {"wayland", "x11"}:
        return explicit
    if _gnome_wayland_session():
        # Electron 39 + native Wayland often fails GNOME portal parent-window association;
        # X11 ozone uses XWayland desktopCapturer which is reliable once Screen Recording is granted.
        return "x11"
    wayland = bool((os.environ.get("WAYLAND_DISPLAY") or "").strip()) or (
        os.environ.get("XDG_SESSION_TYPE", "").strip().lower() == "wayland"
    )
    if wayland:
        return "wayland"
    return "x11"


def _allow_native_wayland_on_gnome() -> bool:
    return os.environ.get("VDISPLAY_ELECTRON_ALLOW_WAYLAND", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def _resolve_ozone_platform(args: argparse.Namespace) -> tuple[str, str | None]:
    explicit_arg = getattr(args, "ozone_platform", None)
    explicit_env = os.environ.get("VDISPLAY_ELECTRON_OZONE_PLATFORM", "").strip().lower()
    if explicit_arg in {"wayland", "x11"}:
        requested = str(explicit_arg)
    elif explicit_env in {"wayland", "x11"}:
        requested = explicit_env
    else:
        requested = _default_ozone_platform()
    if (
        requested == "wayland"
        and _gnome_wayland_session()
        and not _allow_native_wayland_on_gnome()
    ):
        return (
            "x11",
            "overrode --ozone-platform wayland → x11 on GNOME "
            "(set VDISPLAY_ELECTRON_ALLOW_WAYLAND=1 to force native Wayland)",
        )
    return requested, None


def _start_env(args: argparse.Namespace) -> dict[str, str]:
    env = os.environ.copy()
    env.pop("ELECTRON_RUN_AS_NODE", None)
    env.pop("GSETTINGS_SCHEMA_DIR", None)
    env["XDG_DATA_DIRS"] = env.get(
        "VDISPLAY_ELECTRON_XDG_DATA_DIRS",
        "/usr/share/ubuntu:/usr/share/gnome:/usr/local/share:/usr/share:/var/lib/snapd/desktop",
    )
    env.setdefault("VDISPLAY_ELECTRON_GTK_VERSION", "3")
    env.setdefault("LIBVA_DRIVER_NAME", "none")
    ozone, override_note = _resolve_ozone_platform(args)
    env["VDISPLAY_ELECTRON_OZONE_PLATFORM"] = ozone
    if override_note:
        env["VDISPLAY_ELECTRON_OZONE_OVERRIDE"] = override_note
    if ozone == "wayland":
        env.setdefault("VDISPLAY_ELECTRON_MAIN_CAPTURE_FALLBACK", "1")
    env["VDISPLAY_ELECTRON_SHARE_HOST"] = str(args.host)
    env["VDISPLAY_ELECTRON_SHARE_PORT"] = str(args.port)
    env["VDISPLAY_ELECTRON_SHARE_INSTANCE"] = _resolve_instance(args)
    env["VDISPLAY_ELECTRON_TARGET_LABEL"] = _resolve_target(args)
    source = _resolve_source(args)
    env["VDISPLAY_ELECTRON_BRIDGE_SOURCE"] = source
    env["VDISPLAY_ELECTRON_SHARE_SOURCE"] = source
    env.update(_preferred_display_env_for_source(source))
    env["VDISPLAY_ELECTRON_SHARE_MODE"] = str(args.mode)
    env["VDISPLAY_ELECTRON_ALWAYS_ON_TOP"] = "0" if args.no_always_on_top else "1"
    if getattr(args, "no_system_picker", False):
        use_system_picker = False
    elif getattr(args, "system_picker", False):
        use_system_picker = True
    else:
        use_system_picker = os.environ.get("VDISPLAY_ELECTRON_SHARE_USE_SYSTEM_PICKER", "").strip() == "1"
    env["VDISPLAY_ELECTRON_SHARE_USE_SYSTEM_PICKER"] = "1" if use_system_picker else "0"
    env.setdefault("VDISPLAY_ELECTRON_ALLOW_SOURCE_PREVIEWS", "0")
    unsafe_auto_capture = str(os.environ.get("VDISPLAY_ELECTRON_UNSAFE_AUTO_CAPTURE") or "").strip() == "1"
    env["VDISPLAY_ELECTRON_UNSAFE_AUTO_CAPTURE"] = "1" if unsafe_auto_capture else "0"
    env["VDISPLAY_ELECTRON_REMOTE_START_CAPTURE"] = (
        "1"
        if str(os.environ.get("VDISPLAY_ELECTRON_REMOTE_START_CAPTURE") or "").strip() == "1"
        and str(os.environ.get("VDISPLAY_ELECTRON_ALLOW_REMOTE_START_CAPTURE") or "").strip() == "1"
        and unsafe_auto_capture
        else "0"
    )
    agent_url = _resolve_agent_url(args)
    if agent_url:
        env["VDISPLAY_ELECTRON_AGENT_URL"] = agent_url
        env["VDISPLAY_AGENT_URL"] = agent_url
        parsed = urlparse(agent_url)
        if parsed.hostname:
            env["VDISPLAY_AGENT_HOST"] = str(parsed.hostname)
        if parsed.port:
            env["VDISPLAY_AGENT_PORT"] = str(parsed.port)
        env["VDISPLAY_ELECTRON_AUTO_RESUME_CAPTURE"] = (
            "1"
            if str(os.environ.get("VDISPLAY_ELECTRON_AUTO_RESUME_CAPTURE") or "").strip() == "1"
            and str(os.environ.get("VDISPLAY_ELECTRON_ALLOW_AUTO_RESUME_CAPTURE") or "").strip() == "1"
            and unsafe_auto_capture
            else "0"
        )
        env["VDISPLAY_ELECTRON_AUTO_START_CAPTURE"] = (
            "1"
            if str(os.environ.get("VDISPLAY_ELECTRON_AUTO_START_CAPTURE") or "").strip() == "1"
            and str(os.environ.get("VDISPLAY_ELECTRON_ALLOW_AUTO_START_CAPTURE") or "").strip() == "1"
            and unsafe_auto_capture
            else "0"
        )
    else:
        env["VDISPLAY_ELECTRON_AUTO_RESUME_CAPTURE"] = "0"
    if args.no_agent_bridge:
        env["VDISPLAY_ELECTRON_BRIDGE_PUSH"] = "0"
    if getattr(args, "close_quits", False):
        env["VDISPLAY_ELECTRON_CLOSE_QUITS"] = "1"
    return env


def _print_start_hints(args: argparse.Namespace, env: dict[str, str] | None = None) -> None:
    share_url = f"http://{args.host}:{args.port}"
    agent_url = _resolve_agent_url(args)
    source = _resolve_source(args)
    ozone = (env or {}).get("VDISPLAY_ELECTRON_OZONE_PLATFORM") or _default_ozone_platform()
    override_note = (env or {}).get("VDISPLAY_ELECTRON_OZONE_OVERRIDE") or ""
    print(f"vdisplay electron-share: {share_url}", file=sys.stderr)
    print(f"export VDISPLAY_ELECTRON_SHARE_URL={share_url}", file=sys.stderr)
    print(f"# ozone platform: {ozone} (GNOME Wayland defaults to x11 for reliable capture)", file=sys.stderr)
    if override_note:
        print(f"# {override_note}", file=sys.stderr)
    print(
        "# agent: VDISPLAY_AGENT_PORT=8766 vdisplay-agent serve  (port must match VDISPLAY_AGENT_URL)",
        file=sys.stderr,
    )
    if agent_url and not args.no_agent_bridge:
        print(f"export VDISPLAY_AGENT_URL={agent_url}", file=sys.stderr)
        print(f"export VDISPLAY_ELECTRON_AGENT_URL={agent_url}", file=sys.stderr)
        print(f"# bridge source: {source}", file=sys.stderr)
        print(
            f"# status: curl -s {agent_url}/session/screencast/status | jq '.data | {{capture_ready, keeper_mode}}'",
            file=sys.stderr,
        )
        print(
            f"# optional fallback only if Electron capture fails: {agent_url}/api/web/browser-bridge?source={source}",
            file=sys.stderr,
        )
        print(
            "# GNOME: use one capture path at a time; default is Electron manager Share monitor",
            file=sys.stderr,
        )
    if ozone == "wayland" and _gnome_wayland_session():
        print(
            "# warning: native Wayland often times out on GNOME (portal parent window). Prefer omitting --ozone-platform (uses x11) or pass --ozone-platform x11",
            file=sys.stderr,
        )
    if ozone == "x11":
        print(
            "# x11 ozone: grant Settings → Privacy → Screen Recording for Electron, "
            "pick a monitor in the grid, click Share monitor (whole screen — not an app)",
            file=sys.stderr,
        )
    if not agent_url:
        print(
            "# warning: bridge push disabled — set VDISPLAY_AGENT_URL or pass --agent-url",
            file=sys.stderr,
        )


def handle_start(args: argparse.Namespace) -> int:
    if not hasattr(args, "timeout_s"):
        args.timeout_s = 3.0
    _ensure_app_dir()
    _npm_install_if_requested(args)
    if _manager_alive(args) or _port_open(str(args.host), int(args.port)):
        print(
            f"vdisplay electron-share: stopping existing manager on http://{args.host}:{args.port}",
            file=sys.stderr,
        )
        try:
            handle_stop(args)
        except VDisplayError:
            _stop_process_fallback(int(args.port))
        if not _wait_port_closed(str(args.host), int(args.port)):
            _stop_process_fallback(int(args.port))
            _wait_port_closed(str(args.host), int(args.port))
    env = _start_env(args)
    _print_start_hints(args, env)
    try:
        return _run(_electron_command(env), env=env)
    except KeyboardInterrupt:
        print("vdisplay electron-share: interrupted", file=sys.stderr)
        return 130


def handle_install(args: argparse.Namespace) -> int:
    _ensure_app_dir()
    code = _run(["npm", "install"])
    if code == 0:
        print(f"installed electron share app in {_app_dir()}")
    return code


def handle_build(args: argparse.Namespace) -> int:
    _ensure_app_dir()
    _npm_install_if_requested(args)
    return _run(["npm", "run", "build"])


def handle_path(args: argparse.Namespace) -> int:
    print(_app_dir())
    return 0


def _manager_url(args: argparse.Namespace, path: str = "") -> str:
    root = f"http://{args.host}:{args.port}".rstrip("/")
    suffix = path if path.startswith("/") else f"/{path}" if path else ""
    return f"{root}{suffix}"


def _manager_timeout_s(args: argparse.Namespace) -> float:
    return float(getattr(args, "timeout_s", 3.0))


def _manager_get(args: argparse.Namespace, path: str) -> dict:
    url = _manager_url(args, path)
    try:
        with urllib.request.urlopen(url, timeout=_manager_timeout_s(args)) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise VDisplayError(f"{url}: HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise VDisplayError(f"{url}: {exc.reason}") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise VDisplayError(f"{url}: response is not JSON: {raw[:200]}") from exc


def _print_payload(payload: dict) -> int:
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def handle_status(args: argparse.Namespace) -> int:
    return _print_payload(_manager_get(args, "/status"))


def handle_logs(args: argparse.Namespace) -> int:
    return _print_payload(_manager_get(args, "/logs/export"))


def handle_window(args: argparse.Namespace) -> int:
    return _print_payload(_manager_get(args, f"/window/{args.mode}"))


def handle_stop(args: argparse.Namespace) -> int:
    if not hasattr(args, "timeout_s"):
        args.timeout_s = 3.0
    try:
        code = _print_payload(_manager_get(args, "/quit"))
        _wait_port_closed(str(args.host), int(args.port))
        return code
    except VDisplayError:
        _stop_process_fallback(int(args.port))
        _wait_port_closed(str(args.host), int(args.port))
        return _print_payload(
            {
                "ok": True,
                "stopped": "process_fallback",
                "url": _manager_url(args),
            }
        )


def build_health_payload(
    *,
    manager: dict,
    agent_url: str,
    bridge_status: dict | None,
    screencast_status: dict | None,
    source: str,
) -> dict:
    bridge_data = (bridge_status or {}).get("data") or bridge_status or {}
    screencast_data = (screencast_status or {}).get("data") or screencast_status or {}
    bridge_meta = manager.get("browser_bridge") or {}
    frame = manager.get("frame") or {}
    monitor = (bridge_data.get("monitors") or {}).get(source) or {}
    registered_sources = [
        str(item).strip()
        for item in (bridge_data.get("sources") or bridge_meta.get("sources") or [])
        if str(item).strip()
    ]
    electron_source = str(bridge_meta.get("source") or "").strip()
    raw_last_ingest_ok = str(bridge_meta.get("last_ingest_ok") or "").strip()
    raw_last_ok = str(bridge_meta.get("last_ok") or "").strip()
    bridge_last_ok = raw_last_ingest_ok if raw_last_ingest_ok.startswith("ingest ") else ""
    if not bridge_last_ok and raw_last_ok.startswith("ingest "):
        bridge_last_ok = raw_last_ok
    payload = {
        "ok": True,
        "share_url": manager.get("url"),
        "instance": manager.get("instance"),
        "source": source,
        "sharing": bool(manager.get("sharing")),
        "main_capture_fallback_enabled": bool(manager.get("mainCaptureFallbackEnabled")),
        "bridge_push": bool(bridge_meta.get("enabled")),
        "agent_url": agent_url or None,
        "capture_ready": bool(screencast_data.get("capture_ready") or bridge_data.get("capture_ready")),
        "keeper_mode": screencast_data.get("keeper_mode") or bridge_data.get("keeper_mode"),
        "last_frame_age_ms": monitor.get("age_ms") or frame.get("age_ms"),
        "bridge_id": bridge_data.get("bridge_id") or bridge_meta.get("bridge_id"),
        "bridge_last_ok": bridge_last_ok,
        "bridge_lifecycle_ok": bridge_meta.get("last_lifecycle_ok") or bridge_meta.get("last_ok"),
        "bridge_last_heartbeat_ok": bridge_meta.get("last_heartbeat_ok"),
        "bridge_last_error": bridge_meta.get("last_error"),
        "manager": manager,
        "browser_bridge": bridge_data,
        "screencast": screencast_data,
    }
    if registered_sources and source not in registered_sources:
        active = registered_sources[0]
        payload["source_mismatch"] = {
            "requested_source": source,
            "registered_sources": registered_sources,
            "electron_bridge_source": electron_source or None,
            "message": (
                f"Status requested for '{source}' but the active browser bridge is "
                f"registered for {registered_sources}. Use the matching source everywhere."
            ),
        }
        payload["browser_bridge_url"] = (
            f"{agent_url.rstrip('/')}/api/web/browser-bridge?source={active}" if agent_url else None
        )
    return payload


def handle_health(args: argparse.Namespace) -> int:
    manager = _manager_get(args, "/status")
    manager_agent_url = str(((manager.get("browser_bridge") or {}).get("agent_url") or "")).strip().rstrip("/")
    agent_url = str(getattr(args, "agent_url", None) or manager_agent_url or _resolve_agent_url(args)).strip().rstrip("/")
    source = _resolve_source(args)
    bridge_status = None
    screencast_status = None
    bridge_error = ""
    screencast_error = ""
    if agent_url:
        try:
            bridge_status = _agent_get(agent_url, "/session/browser-bridge/status", timeout_s=args.timeout_s)
        except VDisplayError as exc:
            bridge_error = str(exc)
        try:
            screencast_status = _agent_get(agent_url, "/session/screencast/status", timeout_s=args.timeout_s)
        except VDisplayError as exc:
            screencast_error = str(exc)
    payload = build_health_payload(
        manager=manager,
        agent_url=agent_url,
        bridge_status=bridge_status,
        screencast_status=screencast_status,
        source=source,
    )
    if bridge_error:
        payload["browser_bridge_error"] = bridge_error
    if screencast_error:
        payload["screencast_error"] = screencast_error
    if not payload.get("capture_ready") and not manager.get("sharing"):
        renderer_error = str((manager.get("renderer_status") or {}).get("error") or "")
        mismatch = payload.get("source_mismatch") if isinstance(payload.get("source_mismatch"), dict) else {}
        active_source = str(
            (mismatch.get("registered_sources") or [source])[0] if mismatch else source
        ).strip() or source
        bridge_url = payload.get("browser_bridge_url") or (
            f"{agent_url.rstrip('/')}/api/web/browser-bridge?source={active_source}" if agent_url else None
        )
        payload["browser_bridge_url"] = bridge_url
        if mismatch:
            payload["hint"] = (
                f"{mismatch.get('message')} "
                f"Restart services with the matching source, then use Electron Share monitor. "
                f"Optional browser fallback only if Electron fails: {bridge_url}"
            )
        elif _frame_age_stale(payload.get("last_frame_age_ms")):
            payload["hint"] = (
                f"Frames are stale ({payload.get('last_frame_age_ms')}ms). "
                f"Run: vdisplay services resume --source {source} --port {args.port} "
                "or click Share monitor / Grant via GNOME in the Electron window"
            )
        elif "timed out" in renderer_error.lower() or "not supported" in renderer_error.lower():
            payload["hint"] = (
                "Electron capture is blocked or timed out. Click Share monitor once in the Electron manager "
                f"and select whole monitor {active_source}; optional browser fallback only if Electron fails: {bridge_url}"
                if bridge_url
                else "Electron capture is blocked or timed out. Click Share monitor once in the Electron manager."
            )
        elif "requesting screen capture" in renderer_error.lower() or "gnome screen share" in renderer_error.lower():
            payload["hint"] = (
                "Electron is still requesting capture. Approve the GNOME dialog once for the whole monitor; "
                f"optional browser fallback only if Electron fails: {bridge_url}"
                if bridge_url
                else "Electron is still requesting capture. Approve the GNOME dialog once for the whole monitor."
            )
        else:
            payload["hint"] = (
                f"Electron has no shared frame yet. Click Share monitor once in Electron and select whole monitor {active_source}; "
                f"optional browser fallback only if Electron fails: {bridge_url}"
                if bridge_url
                else f"Electron has no shared frame yet. Click Share monitor once in Electron and select whole monitor {active_source}."
            )
    elif not payload.get("capture_ready") and manager.get("sharing"):
        if _frame_age_stale(payload.get("last_frame_age_ms")):
            payload["hint"] = (
                f"Electron is sharing locally, but frames are stale ({payload.get('last_frame_age_ms')}ms). "
                f"Run: vdisplay services resume --source {source} --port {args.port}"
            )
        else:
            payload["hint"] = "Sharing locally but agent not capture_ready — check agent URL and bridge ingest"
    return _print_payload(payload)


def _frame_age_stale(last_frame_age_ms: int | float | None, *, ttl_ms: float = 5000.0) -> bool:
    if last_frame_age_ms is None:
        return False
    try:
        return float(last_frame_age_ms) > ttl_ms
    except (TypeError, ValueError):
        return False


def handle_bridge_status(args: argparse.Namespace) -> int:
    agent_url = _resolve_agent_url(args)
    if not agent_url:
        raise VDisplayError("agent URL required: set VDISPLAY_AGENT_URL or pass --agent-url")
    bridge = _agent_get(agent_url, "/session/browser-bridge/status", timeout_s=args.timeout_s)
    screencast = _agent_get(agent_url, "/session/screencast/status", timeout_s=args.timeout_s)
    payload = {
        "ok": True,
        "agent_url": agent_url,
        "source": _resolve_source(args),
        "browser_bridge": bridge.get("data") or bridge,
        "screencast": screencast.get("data") or screencast,
    }
    return _print_payload(payload)


def _manager_alive(args: argparse.Namespace) -> bool:
    try:
        _manager_get(args, "/status")
        return True
    except VDisplayError:
        return False


def _manager_matches_args(args: argparse.Namespace, status: dict) -> bool:
    if not isinstance(status, dict) or not status.get("ok"):
        return False

    bridge = status.get("browser_bridge") if isinstance(status.get("browser_bridge"), dict) else {}
    renderer = status.get("renderer_status") if isinstance(status.get("renderer_status"), dict) else {}

    requested_source = _resolve_source(args)
    current_source = str(bridge.get("source") or status.get("source") or "").strip()
    if current_source != requested_source:
        return False

    requested_instance = _resolve_instance(args)
    current_instance = str(status.get("instance") or "").strip()
    if current_instance and current_instance != requested_instance:
        return False

    requested_target = _resolve_target(args)
    current_target = str(
        status.get("targetLabel") or renderer.get("targetLabel") or ""
    ).strip()
    if current_target and current_target != requested_target:
        return False

    return True


def _manager_reusable(args: argparse.Namespace) -> bool:
    try:
        status = _manager_get(args, "/status")
    except VDisplayError:
        return False
    return _manager_matches_args(args, status)


def build_prepare_payload(args: argparse.Namespace) -> dict:
    agent_url = _resolve_agent_url(args)
    source = _resolve_source(args)
    instance = _resolve_instance(args)
    target = _resolve_target(args)
    bridge_url = f"{agent_url.rstrip('/')}/api/web/browser-bridge?source={source}" if agent_url else None
    payload: dict = {
        "ok": False,
        "source": source,
        "instance": instance,
        "target": target,
        "agent_url": agent_url or None,
        "share_url": _manager_url(args),
        "browser_bridge_url": bridge_url,
    }
    if not agent_url:
        payload["hint"] = "Set VDISPLAY_AGENT_URL, then: VDISPLAY_AGENT_PORT=8766 vdisplay-agent serve"
        return payload

    try:
        agent_health = _agent_get(agent_url, "/health", timeout_s=args.timeout_s)
        payload["agent_health"] = agent_health
        if not agent_health.get("ok"):
            payload["hint"] = f"Start agent: VDISPLAY_AGENT_PORT=8766 vdisplay-agent serve (expected {agent_url})"
            return payload
    except VDisplayError as exc:
        payload["agent_error"] = str(exc)
        payload["hint"] = f"Start agent: VDISPLAY_AGENT_PORT=8766 vdisplay-agent serve (expected {agent_url})"
        return payload

    screencast_data: dict = {}
    bridge_data: dict = {}
    try:
        screencast_data = (_agent_get(agent_url, "/session/screencast/status", timeout_s=args.timeout_s).get("data") or {})
    except VDisplayError as exc:
        payload["screencast_error"] = str(exc)
    try:
        bridge_data = (_agent_get(agent_url, "/session/browser-bridge/status", timeout_s=args.timeout_s).get("data") or {})
    except VDisplayError as exc:
        payload["browser_bridge_error"] = str(exc)

    manager: dict | None = None
    try:
        manager = _manager_get(args, "/status")
        payload["manager"] = manager
    except VDisplayError as exc:
        payload["manager_error"] = str(exc)

    capture_ready = bool(
        screencast_data.get("capture_ready")
        or bridge_data.get("capture_ready")
    )
    payload["capture_ready"] = capture_ready
    payload["keeper_mode"] = screencast_data.get("keeper_mode") or bridge_data.get("keeper_mode")
    payload["screencast"] = screencast_data or None
    payload["browser_bridge"] = bridge_data or None

    if capture_ready:
        payload["ok"] = True
        payload["hint"] = (
            "Capture is ready via browser bridge — "
            "vdisplay screenshot and koru autopilot prepare-vdisplay should work"
        )
        return payload

    start_cmd = (
        f"vdisplay electron-share up --instance {instance} --target {target} "
        f"--source {source} --port {args.port} --agent-url {agent_url}"
    )
    payload["steps"] = [
        start_cmd,
        f"In Electron manager click Share monitor and select whole monitor {source}",
        f"Optional fallback only: open Chrome/Chromium browser bridge {bridge_url}",
        f"vdisplay services status --source {source} --agent-url {agent_url} --port {args.port}",
        "koru autopilot prepare-vdisplay --ide jetbrains",
    ]
    manager_error = str(payload.get("manager_error") or "")
    manager_down = "connection refused" in manager_error.lower() or "errno 111" in manager_error.lower()
    if manager and manager.get("sharing"):
        payload["hint"] = "Electron is sharing locally but agent is not capture_ready — check agent URL and ingest"
    elif manager:
        payload["hint"] = (
            f"Electron manager is running; click Share monitor once in Electron and "
            f"select whole monitor {source}. Browser bridge is fallback only: {bridge_url}"
        )
    elif manager_down and bridge_data.get("registered") and _bridge_heartbeat_stale(bridge_data):
        payload["bridge_stale"] = True
        payload["hint"] = (
            f"Electron manager on :{args.port} is not running; agent still has a stale bridge "
            f"({bridge_data.get('bridge_id')}). Start the background manager: {start_cmd}"
        )
    elif manager_down:
        payload["hint"] = (
            f"Electron manager on :{args.port} is not reachable. Start the background manager: {start_cmd}"
        )
    else:
        payload["hint"] = f"Start Electron share: {start_cmd}"
    return payload


def handle_up(args: argparse.Namespace) -> int:
    """Start Electron share in background when manager HTTP is down, then run prepare."""
    if _manager_reusable(args):
        return handle_prepare(args)
    if _manager_alive(args):
        try:
            handle_stop(args)
        except VDisplayError:
            _stop_process_fallback(int(args.port))
        if not _wait_port_closed(str(args.host), int(args.port)):
            _stop_process_fallback(int(args.port))
            _wait_port_closed(str(args.host), int(args.port))

    _ensure_app_dir()
    _npm_install_if_requested(args)
    env = _start_env(args)
    log_path = _app_dir() / f"electron-share-{args.port}.log"
    command = _electron_command(env)
    with log_path.open("ab") as log_file:
        proc = subprocess.Popen(
            command,
            cwd=str(_app_dir()),
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    deadline = time.monotonic() + float(getattr(args, "startup_timeout_s", 25.0))
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            tail = log_path.read_text(encoding="utf-8", errors="replace")[-1200:]
            raise VDisplayError(
                f"electron share exited early (code={proc.returncode}); log tail:\n{tail}"
            )
        if _manager_alive(args):
            payload = build_prepare_payload(args)
            payload["started"] = True
            payload["pid"] = proc.pid
            payload["log_path"] = str(log_path)
            return _print_payload(payload)
        time.sleep(0.4)
    raise VDisplayError(
        f"electron share did not become ready on {_manager_url(args)} within "
        f"{getattr(args, 'startup_timeout_s', 25.0)}s; see {log_path}"
    )


def handle_prepare(args: argparse.Namespace) -> int:
    return _print_payload(build_prepare_payload(args))


def _add_manager_http_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--host", default="127.0.0.1", help="HTTP host")
    parser.add_argument("--port", type=int, default=8799, help="HTTP port")
    parser.add_argument("--timeout-s", type=float, default=3.0, help="HTTP timeout")


def _add_runtime_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--host", default="127.0.0.1", help="HTTP bind host")
    parser.add_argument("--port", type=int, default=8799, help="HTTP bind port")
    parser.add_argument("--timeout-s", type=float, default=3.0, help="HTTP timeout")
    parser.add_argument("--instance", default="jetbrains", help="Instance/tray label")
    parser.add_argument("--target", default="jetbrains", help="Target app/window label")
    parser.add_argument("--source", default="HDMI-1", help="Source name registered in vdisplay-agent bridge")
    parser.add_argument("--agent-url", help="vdisplay-agent URL (defaults to VDISPLAY_AGENT_URL)")
    parser.add_argument(
        "--no-agent-bridge",
        action="store_true",
        help="Disable push bridge to vdisplay-agent even when an agent URL is configured",
    )
    parser.add_argument(
        "--mode",
        choices=("compact", "full"),
        default="full",
        help="Initial manager window mode",
    )
    parser.add_argument(
        "--no-always-on-top",
        action="store_true",
        help="Disable default always-on-top manager window",
    )
    parser.add_argument(
        "--system-picker",
        action="store_true",
        help="Use GNOME/Chromium system picker (opt-in; default shares whole monitor via grid)",
    )
    parser.add_argument(
        "--no-system-picker",
        action="store_true",
        help="Explicitly disable system picker (default since monitor-first flow)",
    )
    parser.add_argument(
        "--ozone-platform",
        choices=("wayland", "x11"),
        help="Electron Ozone platform; on GNOME Wayland defaults to x11 (reliable capture). Pass wayland only if needed.",
    )
    parser.add_argument(
        "--close-quits",
        action="store_true",
        help="Make window close quit instead of hiding to tray",
    )


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser(
        "electron-share",
        help="Run the optional Electron screen-share manager",
    )
    action = parser.add_subparsers(dest="electron_share_action", required=True)

    start = action.add_parser("start", help="Start the Electron share manager")
    _add_runtime_args(start)
    start.add_argument(
        "--install",
        action="store_true",
        help="Run npm install before starting, useful for first run",
    )
    start.set_defaults(func=handle_start)

    install = action.add_parser("install", help="Run npm install for the Electron share manager")
    install.set_defaults(func=handle_install)

    build = action.add_parser("build", help="Build/package the Electron share manager")
    build.add_argument(
        "--install",
        action="store_true",
        help="Run npm install before build",
    )
    build.set_defaults(func=handle_build)

    path_parser = action.add_parser("path", help="Print the Electron share app directory")
    path_parser.set_defaults(func=handle_path)

    status = action.add_parser("status", help="Read Electron share manager status")
    _add_manager_http_args(status)
    status.set_defaults(func=handle_status)

    logs = action.add_parser("logs", help="Export current Electron share session logs to markdown")
    _add_manager_http_args(logs)
    logs.set_defaults(func=handle_logs)

    window = action.add_parser("window", help="Control the Electron share manager window")
    _add_manager_http_args(window)
    window.add_argument("mode", choices=("full", "compact", "tray", "show"), help="Window mode/action")
    window.set_defaults(func=handle_window)

    stop = action.add_parser("stop", help="Stop one Electron share manager instance")
    _add_manager_http_args(stop)
    stop.set_defaults(func=handle_stop)

    health = action.add_parser(
        "health",
        help="Combined Electron share + vdisplay-agent browser-bridge health",
    )
    _add_manager_http_args(health)
    health.add_argument("--agent-url", help="vdisplay-agent URL (defaults to VDISPLAY_AGENT_URL)")
    health.add_argument("--source", default="HDMI-1", help="Registered bridge source name")
    health.set_defaults(func=handle_health)

    bridge = action.add_parser(
        "bridge-status",
        help="Read vdisplay-agent browser-bridge and screencast status",
    )
    bridge.add_argument("--agent-url", help="vdisplay-agent URL (defaults to VDISPLAY_AGENT_URL)")
    bridge.add_argument("--source", default="HDMI-1", help="Registered bridge source name")
    bridge.add_argument("--timeout-s", type=float, default=3.0, help="HTTP timeout")
    bridge.set_defaults(func=handle_bridge_status)

    prepare = action.add_parser(
        "prepare",
        help="Check agent + Electron bridge readiness and print next steps",
    )
    _add_runtime_args(prepare)
    prepare.set_defaults(func=handle_prepare)

    up = action.add_parser(
        "up",
        help="Start Electron share if needed, then run prepare checks",
    )
    _add_runtime_args(up)
    up.add_argument(
        "--startup-timeout-s",
        type=float,
        default=25.0,
        help="Seconds to wait for Electron HTTP after start",
    )
    up.add_argument(
        "--install",
        action="store_true",
        help="Run npm install before starting, useful for first run",
    )
    up.set_defaults(func=handle_up)
