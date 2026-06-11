"""Load project ``.env`` files and parse ``VDISPLAY_*`` variables."""

from __future__ import annotations

import os
from pathlib import Path

_LOADED_PATHS: set[str] = set()


def load_project_env(project: str | Path = ".") -> Path | None:
    """Load ``.env`` and ``.vdisplay/.env`` once (does not override existing os.environ)."""
    root = Path(project).expanduser().resolve()
    last: Path | None = None
    for candidate in (root / ".env", root / ".vdisplay" / ".env"):
        key = str(candidate.resolve())
        if key in _LOADED_PATHS:
            continue
        if candidate.is_file():
            _load_env_file(candidate)
            _LOADED_PATHS.add(key)
            last = candidate
    return last


def _load_env_file(path: Path) -> None:
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key or key in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ[key] = value


def env_csv(name: str) -> list[str] | None:
    if name not in os.environ:
        return None
    raw = os.environ[name].strip()
    if not raw:
        return []
    return [part.strip() for part in raw.split(",")]


def env_dict_int(name: str) -> dict[str, int] | None:
    if name not in os.environ:
        return None
    raw = os.environ[name].strip()
    if not raw:
        return {}
    parsed: dict[str, int] = {}
    for part in raw.split(","):
        piece = part.strip()
        if not piece or "=" not in piece:
            continue
        key, value = piece.split("=", 1)
        try:
            parsed[key.strip()] = int(value.strip())
        except ValueError:
            continue
    return parsed


def env_int(name: str) -> int | None:
    if name not in os.environ:
        return None
    raw = os.environ[name].strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def env_bool(name: str) -> bool | None:
    if name not in os.environ:
        return None
    raw = os.environ[name].strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    return None


def env_str(name: str) -> str | None:
    if name not in os.environ:
        return None
    return os.environ[name]
