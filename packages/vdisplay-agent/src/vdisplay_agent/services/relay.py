"""Window adopt/release via relay session."""

from __future__ import annotations

from typing import Any

from ..session_store import SessionStore


def adopt_window(store: SessionStore, body: dict[str, Any]) -> dict[str, Any]:
    relay = store.relay_session(body.get("session_id"))
    window_id = relay.adopt_window(
        match_title=body.get("match_title") or body.get("title"),
        window_id=body.get("window_id"),
        match_class=body.get("match_class") or body.get("wm_class"),
        match_pid=body.get("match_pid") or body.get("pid"),
        match_app=body.get("match_app") or body.get("app"),
        target=body.get("target") or "offscreen",
    )
    return {"ok": True, "window_id": window_id, "adopted": relay.list_adopted()}


def release_window(store: SessionStore, body: dict[str, Any]) -> dict[str, Any]:
    relay = store.relay_session(body.get("session_id"))
    window_id = relay.release_window(
        match_title=body.get("match_title") or body.get("title"),
        window_id=body.get("window_id"),
        match_class=body.get("match_class") or body.get("wm_class"),
        match_pid=body.get("match_pid") or body.get("pid"),
        match_app=body.get("match_app") or body.get("app"),
    )
    return {"ok": True, "window_id": window_id, "adopted": relay.list_adopted()}
