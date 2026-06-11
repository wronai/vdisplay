"""Append broker HTTP errors and screencast lifecycle events to .vdisplay/broker.jsonl."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


def _broker_log_path() -> Path:
    session_dir = os.environ.get("VDISPLAY_SESSION_DIR", "").strip()
    if session_dir:
        return Path(session_dir).expanduser().parent / "broker.jsonl"
    project = Path.cwd() / ".vdisplay" / "broker.jsonl"
    if project.parent.is_dir() or Path.cwd().name == "vdisplay":
        return project
    return Path.home() / ".vdisplay" / "broker.jsonl"


def log_broker_event(action: str, *, ok: bool, error: str | None = None, **fields: Any) -> None:
    path = _broker_log_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "action": action,
            "ok": ok,
            **fields,
        }
        if error:
            record["error"] = error
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass
