"""Persist browser sessions across CLI invocations via CDP."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from ..exceptions import VDisplayError

_SESSION_ROOT = Path.home() / ".cache" / "vdisplay" / "browser-sessions"


@dataclass(frozen=True)
class DetachedBrowserMeta:
    session_id: str
    cdp_url: str
    pid: int
    url: str
    engine: str
    headless: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def detached_sessions_enabled() -> bool:
    from ..application.env_defaults import env_flag

    return env_flag("VDISPLAY_BROWSER_DETACHED", default=True)


def meta_path(session_id: str) -> Path:
    return _SESSION_ROOT / f"{session_id}.json"


def profile_dir(session_id: str) -> Path:
    return _SESSION_ROOT / session_id / "profile"


def save_meta(meta: DetachedBrowserMeta) -> None:
    _SESSION_ROOT.mkdir(parents=True, exist_ok=True)
    meta_path(meta.session_id).write_text(json.dumps(meta.to_dict(), indent=2), encoding="utf-8")


def load_meta(session_id: str) -> DetachedBrowserMeta | None:
    path = meta_path(session_id)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return DetachedBrowserMeta(
            session_id=str(payload["session_id"]),
            cdp_url=str(payload["cdp_url"]),
            pid=int(payload["pid"]),
            url=str(payload.get("url") or ""),
            engine=str(payload.get("engine") or "chromium"),
            headless=bool(payload.get("headless", True)),
        )
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def remove_meta(session_id: str) -> None:
    path = meta_path(session_id)
    if path.is_file():
        path.unlink()


def process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _chromium_executable() -> Path:
    root = Path.home() / ".cache" / "ms-playwright"
    matches = sorted(root.glob("chromium-*/chrome-linux*/chrome"))
    if not matches:
        raise VDisplayError("Chromium not installed — run: playwright install chromium")
    return matches[-1]


def wait_for_cdp(cdp_url: str, *, timeout_s: float = 30.0) -> None:
    deadline = time.monotonic() + timeout_s
    version_url = cdp_url.rstrip("/") + "/json/version"
    while time.monotonic() < deadline:
        try:
            with urlopen(version_url, timeout=1.0) as response:
                if response.status == 200:
                    return
        except (URLError, TimeoutError, OSError):
            time.sleep(0.2)
    raise VDisplayError(f"CDP endpoint did not become ready: {cdp_url}")


def launch_detached_chromium(
    *,
    session_id: str,
    url: str,
    headless: bool,
) -> DetachedBrowserMeta:
    if not detached_sessions_enabled():
        raise VDisplayError("detached browser sessions disabled")

    existing = load_meta(session_id)
    if existing is not None and process_alive(existing.pid):
        raise VDisplayError(f"browser session already exists: {session_id}")

    port = find_free_port()
    user_data = profile_dir(session_id)
    user_data.mkdir(parents=True, exist_ok=True)
    chrome = _chromium_executable()
    args = [
        str(chrome),
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data}",
        "--no-first-run",
        "--no-default-browser-check",
        "--no-sandbox",
        "--disable-dev-shm-usage",
    ]
    if headless:
        args.append("--headless=new")
    if url:
        args.append(url)
    proc = subprocess.Popen(
        args,
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    cdp_url = f"http://127.0.0.1:{port}"
    try:
        wait_for_cdp(cdp_url)
    except VDisplayError:
        proc.kill()
        raise
    meta = DetachedBrowserMeta(
        session_id=session_id,
        cdp_url=cdp_url,
        pid=proc.pid,
        url=url,
        engine="chromium",
        headless=headless,
    )
    save_meta(meta)
    return meta


def stop_detached(session_id: str) -> None:
    meta = load_meta(session_id)
    if meta is None:
        return
    if process_alive(meta.pid):
        try:
            os.kill(meta.pid, 15)
        except (ProcessLookupError, PermissionError):
            pass
    remove_meta(session_id)
    profile = profile_dir(session_id)
    if profile.is_dir():
        try:
            import shutil

            shutil.rmtree(profile, ignore_errors=True)
        except Exception:
            pass


def session_available(session_id: str) -> bool:
    meta = load_meta(session_id)
    if meta is None:
        return False
    if not process_alive(meta.pid):
        remove_meta(session_id)
        return False
    return True
