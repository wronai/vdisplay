"""Execute automation task commands via DSL, vdisplay CLI, shell, or HTTP API."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from typing import Any

from ...exceptions import VDisplayError

_DSL_VERBS = frozenset({
    "SCREENSHOT",
    "VIRTUAL_START",
    "VIRTUAL_STOP",
    "LAUNCH",
    "MIRROR",
    "ADOPT",
    "RELEASE",
    "CONTROL_CLICK",
    "CONTROL_FOCUS",
    "CONTROL_SET_VALUE",
    "TERMINAL_OPEN",
    "BROWSER_OPEN",
    "CONTROLS_LIST",
    "CONTROLS_FIND",
    "HEALTH",
    "INFO",
    "OUTPUTS",
    "MONITORS",
    "WINDOWS",
    "ALL",
    "CAPABILITIES",
    "VALIDATE",
    "DIAGNOSE_CONTROL",
})


@dataclass
class ExecuteResult:
    ok: bool
    method: str
    output: str = ""
    error: str = ""
    exit_code: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "method": self.method,
            "output": self.output,
            "error": self.error,
            "exit_code": self.exit_code,
        }


def execute_task_command(command: str, *, project: str | None = None, dry_run: bool = False) -> ExecuteResult:
    cmd = command.strip()
    if not cmd:
        return ExecuteResult(ok=False, method="empty", error="empty command")

    if dry_run:
        return ExecuteResult(ok=True, method="dry-run", output=cmd)

    if cmd.startswith("__api__:"):
        return _execute_api(json.loads(cmd[len("__api__:") :]))

    kind = _detect_kind(cmd)
    if kind == "dsl":
        return _execute_dsl(cmd)
    if kind == "vdisplay":
        return _execute_vdisplay_cli(cmd, project=project)
    return _execute_shell(cmd, project=project)


def _detect_kind(command: str) -> str:
    stripped = command.strip()
    upper = stripped.upper()
    first = upper.split(None, 1)[0] if upper else ""
    if first in _DSL_VERBS:
        return "dsl"
    if stripped.lower().startswith("terminal open") or stripped.lower().startswith("browser open"):
        return "dsl"
    if stripped.startswith("vdisplay ") or stripped == "vdisplay":
        return "vdisplay"
    if stripped.startswith("dsl2vdisplay "):
        return "dsl"
    return "shell"


def _execute_dsl(command: str) -> ExecuteResult:
    try:
        from dsl2vdisplay.bus import dispatch, execute_dsl_line
    except ImportError as exc:
        return ExecuteResult(ok=False, method="dsl", error=f"dsl2vdisplay not installed: {exc}")

    line = command.strip()
    if line.lower().startswith("dsl2vdisplay "):
        line = line[len("dsl2vdisplay ") :].strip()
        if line.startswith("-c "):
            line = shlex.split(line[3:])[0] if line[3:].strip() else ""

    result = execute_dsl_line(line) if hasattr(execute_dsl_line, "__call__") else dispatch(line)
    output = result.output or ""
    if not output and getattr(result, "data", None):
        output = json.dumps(result.data, indent=2)
    return ExecuteResult(
        ok=bool(result.ok),
        method="dsl",
        output=output,
        error=str(getattr(result, "error", "") or ""),
        exit_code=0 if result.ok else 1,
    )


def _execute_vdisplay_cli(command: str, *, project: str | None) -> ExecuteResult:
    import io
    from contextlib import redirect_stderr, redirect_stdout

    argv = shlex.split(command)
    if not argv or argv[0] != "vdisplay":
        return ExecuteResult(ok=False, method="vdisplay-cli", error="expected vdisplay subcommand")

    from ...cli import main

    stdout = io.StringIO()
    stderr = io.StringIO()
    previous_cwd = os.getcwd()
    try:
        if project:
            os.chdir(project)
        # Reset any probe cache so sub-invocation sees the current VDISPLAY_AGENT_URL fresh
        try:
            from ...agent_config import reset_agent_probe_cache
            reset_agent_probe_cache()
        except Exception:
            pass
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = int(main(argv[1:]))
    except SystemExit as exc:
        code = exc.code
        exit_code = int(code) if isinstance(code, int) else (0 if code is None else 1)
    except Exception as exc:
        # Don't let transient agent issues in enrichment kill basic vdisplay subcommands
        # (e.g. monitors enrichment trying agent while screencast is starting up)
        stderr.write(f"subcommand error: {exc}\n")
        exit_code = 1
    finally:
        os.chdir(previous_cwd)

    return ExecuteResult(
        ok=exit_code == 0,
        method="vdisplay-cli",
        output=stdout.getvalue().strip(),
        error=stderr.getvalue().strip(),
        exit_code=exit_code,
    )


def _execute_shell(command: str, *, project: str | None) -> ExecuteResult:
    proc = subprocess.run(
        ["bash", "-lc", command],
        capture_output=True,
        text=True,
        cwd=project or None,
        env=os.environ.copy(),
    )
    return ExecuteResult(
        ok=proc.returncode == 0,
        method="shell",
        output=(proc.stdout or "").strip(),
        error=(proc.stderr or "").strip(),
        exit_code=int(proc.returncode),
    )


def _execute_api(payload: dict[str, Any]) -> ExecuteResult:
    endpoint = str(payload.get("endpoint") or "").strip()
    if not endpoint:
        return ExecuteResult(ok=False, method="api", error="missing api endpoint")
    method = str(payload.get("method") or "GET").upper()
    headers = dict(payload.get("headers") or {})
    body = payload.get("body")
    try:
        import urllib.error
        import urllib.request

        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")
        request = urllib.request.Request(endpoint, data=data, headers=headers, method=method)
        with urllib.request.urlopen(request, timeout=float(payload.get("timeout", 30))) as response:
            text = response.read().decode("utf-8", errors="replace")
        return ExecuteResult(ok=True, method="api", output=text)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return ExecuteResult(ok=False, method="api", error=f"HTTP {exc.code}: {detail}", exit_code=exc.code)
    except Exception as exc:
        return ExecuteResult(ok=False, method="api", error=str(exc))
