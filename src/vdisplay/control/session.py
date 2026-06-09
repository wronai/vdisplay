"""Unified session metadata and catalog — shared by agent, CLI, and control plane."""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field

from .session_kind import SessionKind

_LEGACY_KIND_MAP: dict[str, SessionKind] = {
    "virtual": SessionKind.VIRTUAL,
    "mirror": SessionKind.MIRROR,
    "relay": SessionKind.RELAY,
    "terminal": SessionKind.TERMINAL,
    "browser": SessionKind.BROWSER,
    "screencast": SessionKind.SCREENCAST,
    "capture_sampler": SessionKind.CAPTURE_SAMPLER,
    "sampler": SessionKind.CAPTURE_SAMPLER,
}


def parse_session_kind(kind: str | SessionKind) -> SessionKind:
    if isinstance(kind, SessionKind):
        return kind
    normalized = str(kind).strip().lower()
    if normalized in _LEGACY_KIND_MAP:
        return _LEGACY_KIND_MAP[normalized]
    return SessionKind(normalized)


class SessionMetadata(BaseModel):
    """Portable session record for APIs and diagnostics."""

    session_id: str
    kind: SessionKind
    started: bool = True
    source: str = "agent"
    command: str | None = None
    title: str | None = None
    display: str | None = None
    capabilities: dict[str, Any] = Field(default_factory=dict)
    info: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = self.model_dump()
        payload["kind"] = self.kind.value
        return payload


class SessionCatalog(BaseModel):
    sessions: list[SessionMetadata] = Field(default_factory=list)
    counts: dict[str, int] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sessions": [item.to_dict() for item in self.sessions],
            "counts": self.counts,
            "total": len(self.sessions),
        }


class AgentSessionStore(Protocol):
    sessions: dict[str, Any]
    relay: Any | None
    screencast: Any | None
    sampler: Any | None


def _safe_info(handle: Any) -> dict[str, Any]:
    info = getattr(handle, "info", None)
    if callable(info):
        try:
            payload = info()
            if isinstance(payload, dict):
                return payload
        except Exception:
            return {}
    return {}


def _safe_capabilities(handle: Any) -> dict[str, Any]:
    caps = getattr(handle, "capabilities", None)
    if callable(caps):
        try:
            payload = caps()
            if isinstance(payload, dict):
                return payload
        except Exception:
            return {}
    return {}


def metadata_from_agent_record(record: Any, *, source: str = "agent") -> SessionMetadata:
    kind = parse_session_kind(getattr(record, "kind", SessionKind.VIRTUAL.value))
    handle = getattr(record, "handle", None)
    command = getattr(handle, "command", None)
    title = getattr(handle, "title", None)
    return SessionMetadata(
        session_id=str(getattr(record, "session_id", "")),
        kind=kind,
        started=bool(getattr(record, "started", True)),
        source=source,
        command=command,
        title=title,
        capabilities=_safe_capabilities(handle),
        info=_safe_info(handle),
    )


def metadata_from_browser_session(session: Any, *, source: str = "local") -> SessionMetadata:
    return SessionMetadata(
        session_id=str(session.session_id),
        kind=SessionKind.BROWSER,
        started=bool(getattr(session, "_alive", True)),
        source=source,
        title=getattr(session, "title", None),
        info={"url": session.url, "headless": session.headless},
    )


def metadata_from_terminal_session(session: Any, *, source: str = "local") -> SessionMetadata:
    return SessionMetadata(
        session_id=str(session.session_id),
        kind=SessionKind.TERMINAL,
        started=bool(getattr(session, "_alive", True)),
        source=source,
        command=getattr(session, "command", None),
        title=getattr(session, "title", None),
        info={"rows": session.screen.rows, "cols": session.screen.cols},
    )


def build_catalog_from_agent_store(store: AgentSessionStore) -> SessionCatalog:
    """Enumerate broker-owned sessions including ephemeral screencast/sampler handles."""
    items: list[SessionMetadata] = []

    for record in store.sessions.values():
        items.append(metadata_from_agent_record(record))

    screencast = store.screencast
    if screencast is not None:
        status = {}
        status_fn = getattr(screencast, "status", None)
        if callable(status_fn):
            try:
                status = status_fn()
            except Exception:
                status = {}
        items.append(
            SessionMetadata(
                session_id="screencast:active",
                kind=SessionKind.SCREENCAST,
                source="agent",
                info=status if isinstance(status, dict) else {},
            )
        )

    sampler = store.sampler
    if sampler is not None:
        status = {}
        status_fn = getattr(sampler, "status", None)
        if callable(status_fn):
            try:
                status = status_fn()
            except Exception:
                status = {}
        items.append(
            SessionMetadata(
                session_id="sampler:active",
                kind=SessionKind.CAPTURE_SAMPLER,
                source="agent",
                info=status if isinstance(status, dict) else {},
            )
        )

    counts: dict[str, int] = {}
    for item in items:
        key = item.kind.value
        counts[key] = counts.get(key, 0) + 1

    return SessionCatalog(sessions=items, counts=counts)


def build_catalog_local() -> SessionCatalog:
    """Terminal and browser sessions registered in-process (CLI / local executor)."""
    from .providers.browser_session import default_registry as browser_registry
    from .providers.terminal_session import default_registry as terminal_registry

    items: list[SessionMetadata] = []
    for session in getattr(terminal_registry(), "_sessions", {}).values():
        items.append(metadata_from_terminal_session(session, source="local"))
    for session in getattr(browser_registry(), "_sessions", {}).values():
        items.append(metadata_from_browser_session(session, source="local"))

    counts: dict[str, int] = {}
    for item in items:
        key = item.kind.value
        counts[key] = counts.get(key, 0) + 1
    return SessionCatalog(sessions=items, counts=counts)


def merge_catalogs(*catalogs: SessionCatalog) -> SessionCatalog:
    seen: set[str] = set()
    merged: list[SessionMetadata] = []
    for catalog in catalogs:
        for item in catalog.sessions:
            if item.session_id in seen:
                continue
            seen.add(item.session_id)
            merged.append(item)
    counts: dict[str, int] = {}
    for item in merged:
        key = item.kind.value
        counts[key] = counts.get(key, 0) + 1
    return SessionCatalog(sessions=merged, counts=counts)
