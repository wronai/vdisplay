"""Unified session catalog (PR-10)."""

from __future__ import annotations

from vdisplay.control.session import (
    SessionKind,
    build_catalog_from_agent_store,
    build_catalog_local,
    merge_catalogs,
    parse_session_kind,
)
from vdisplay.control.providers.terminal_session import default_registry
from vdisplay_agent.session_store import SessionRecord, SessionStore


def test_parse_session_kind_legacy_strings() -> None:
    assert parse_session_kind("virtual") is SessionKind.VIRTUAL
    assert parse_session_kind("terminal") is SessionKind.TERMINAL
    assert parse_session_kind(SessionKind.MIRROR) is SessionKind.MIRROR


def test_build_catalog_from_agent_store() -> None:
    store = SessionStore()
    store.register(kind="virtual", handle=_FakeHandle(), prefix="virt")
    store.register(kind="terminal", handle=_TerminalHandle(), prefix="term")

    catalog = build_catalog_from_agent_store(store)
    assert len(catalog.sessions) == 2
    kinds = {item.kind for item in catalog.sessions}
    assert SessionKind.VIRTUAL in kinds
    assert SessionKind.TERMINAL in kinds
    assert catalog.counts["virtual"] == 1
    assert catalog.counts["terminal"] == 1


def test_build_catalog_local_terminal() -> None:
    registry = default_registry()
    registry.open_mock(lines=["READY"], session_id="term-local-1")
    catalog = build_catalog_local()
    assert len(catalog.sessions) >= 1
    assert any(item.session_id == "term-local-1" for item in catalog.sessions)
    registry.close("term-local-1")


def test_merge_catalogs_dedupes_by_id() -> None:
    from vdisplay.control.session import SessionMetadata

    left = build_catalog_local()
    right = build_catalog_local()
    merged = merge_catalogs(left, right)
    ids = [item.session_id for item in merged.sessions]
    assert len(ids) == len(set(ids))


class _FakeHandle:
    def info(self) -> dict:
        return {"display": ":99"}

    def capabilities(self) -> dict:
        return {"input": True}


class _TerminalHandle:
    command = "bash"
    title = "shell"

    def info(self) -> dict:
        return {}

    def capabilities(self) -> dict:
        return {}
