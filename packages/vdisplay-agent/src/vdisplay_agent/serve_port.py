"""Stop a prior vdisplay-agent broker before binding serve."""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterable


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _parse_ss_pids(output: str) -> list[int]:
    pids: list[int] = []
    for match in re.finditer(r"pid=(\d+)", output):
        pids.append(int(match.group(1)))
    return pids


def _pids_from_ss(port: int) -> list[int]:
    try:
        result = subprocess.run(
            ["ss", "-tlnp", f"sport = :{port}"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    return _parse_ss_pids(result.stdout)


def _pids_from_lsof(port: int) -> list[int]:
    try:
        result = subprocess.run(
            ["lsof", "-ti", f"tcp:{port}"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    pids: list[int] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.isdigit():
            pids.append(int(line))
    return pids


def find_listener_pids(port: int) -> list[int]:
    """Return PIDs listening on TCP port (best effort)."""
    pids = _pids_from_ss(port)
    if not pids:
        pids = _pids_from_lsof(port)
    current = os.getpid()
    return sorted({pid for pid in pids if pid != current})


def _cmdline(pid: int) -> str:
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return ""
    return raw.replace(b"\x00", b" ").decode("utf-8", errors="replace").strip()


def _is_vdisplay_agent_pid(pid: int) -> bool:
    cmd = _cmdline(pid).lower()
    return "vdisplay-agent" in cmd or "vdisplay_agent" in cmd


def _partition_listener_pids(pids: Iterable[int]) -> tuple[list[int], list[int]]:
    agent: list[int] = []
    other: list[int] = []
    for pid in pids:
        if pid == os.getpid():
            continue
        if _is_vdisplay_agent_pid(pid):
            agent.append(pid)
        else:
            other.append(pid)
    return sorted(agent), sorted(other)


def _probe_is_vdisplay_agent(host: str, port: int) -> bool:
    url = f"http://{host}:{port}/health"
    try:
        with urllib.request.urlopen(url, timeout=0.5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
        return False
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    service = data.get("service") if isinstance(data, dict) else None
    broker = data.get("broker") if isinstance(data, dict) else None
    return service == "vdisplay-agent" or broker == "vdisplay-agent"


def stop_pids(pids: Iterable[int], *, host: str, port: int) -> list[int]:
    """SIGTERM then SIGKILL broker PIDs; return PIDs we attempted to stop."""
    targets = [pid for pid in pids if pid != os.getpid()]
    if not targets:
        return []

    for pid in targets:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        if not any(_pid_alive(pid) for pid in targets):
            break
        time.sleep(0.1)

    for pid in targets:
        if _pid_alive(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    for pid in targets:
        print(
            f"Stopped previous vdisplay-agent (pid {pid}) on {host}:{port}",
            file=sys.stderr,
        )
    return targets


def ensure_broker_port_free(host: str, port: int) -> None:
    """
    If port is held by vdisplay-agent, stop it so serve can bind.
    Raises RuntimeError when another service owns the port.
    """
    pids = find_listener_pids(port)
    if not pids:
        return

    agent_pids, other_pids = _partition_listener_pids(pids)
    if agent_pids:
        stop_pids(agent_pids, host=host, port=port)
        try:
            from vdisplay.agent_config import reset_agent_probe_cache

            reset_agent_probe_cache()
        except ImportError:
            pass
        if not find_listener_pids(port):
            return
        agent_pids, other_pids = _partition_listener_pids(find_listener_pids(port))

    if other_pids and _probe_is_vdisplay_agent(host, port):
        stop_pids(other_pids, host=host, port=port)
        try:
            from vdisplay.agent_config import reset_agent_probe_cache

            reset_agent_probe_cache()
        except ImportError:
            pass
        return

    remaining = find_listener_pids(port)
    if remaining:
        _, foreign = _partition_listener_pids(remaining)
        blockers = foreign or remaining
        raise RuntimeError(
            f"Port {host}:{port} is already in use (pids={blockers}). "
            "Stop that process or use --port."
        )
