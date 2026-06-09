from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Mapping, Sequence
from typing import Any


def require_command(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise FileNotFoundError(f"Required command not found: {name}")
    return path


def run_command(
    args: Sequence[str],
    *,
    env: Mapping[str, str] | None = None,
    check: bool = True,
    capture_output: bool = True,
    text: bool = False,
    timeout: float | None = 30,
) -> subprocess.CompletedProcess[Any]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        list(args),
        env=merged,
        check=check,
        capture_output=capture_output,
        text=text,
        timeout=timeout,
    )


def run_command_bytes(
    args: Sequence[str],
    *,
    env: Mapping[str, str] | None = None,
    timeout: float | None = 30,
) -> bytes:
    result = run_command(args, env=env, text=False, timeout=timeout)
    return result.stdout
