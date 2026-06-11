"""Replay session discovery for the web console."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from vdisplay.application.env_defaults import env_value
from vdisplay.exceptions import VDisplayError


def list_replay_sessions(root: Path | None = None) -> list[dict[str, Any]]:
    base = root or Path(env_value("VDISPLAY_SESSION_BASE")).expanduser()
    if not base.is_dir():
        return []
    sessions: list[dict[str, Any]] = []
    for path in sorted(base.iterdir(), key=lambda item: item.stat().st_mtime, reverse=True):
        if not path.is_dir():
            continue
        steps_dir = path / "steps"
        step_count = len(list(steps_dir.iterdir())) if steps_dir.is_dir() else 0
        meta: dict[str, Any] = {}
        session_json = path / "session.json"
        if session_json.is_file():
            try:
                meta = json.loads(session_json.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                meta = {}
        sessions.append(
            {
                "session_id": str(meta.get("session_id") or path.name),
                "path": str(path.resolve()),
                "steps": step_count,
                "updated_at": meta.get("updated_at"),
                "source": "audit",
            }
        )
    return sessions


def queue_replay(session_id: str, *, root: Path | None = None) -> dict[str, Any]:
    matches = [item for item in list_replay_sessions(root) if item["session_id"] == session_id]
    if not matches:
        raise VDisplayError(f"replay session not found: {session_id}")
    session = matches[0]
    from vdisplay.application.replay import queue_session_replay

    return queue_session_replay(session["path"])
