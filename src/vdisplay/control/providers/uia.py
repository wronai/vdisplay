"""Windows UIA semantic control provider — PR-21 full invoke."""

from __future__ import annotations

from typing import Any

from ...exceptions import VDisplayError
from ..base import ControlProvider
from ..models import ControlBounds, ControlNode, ControlSnapshot
from ..selector import ControlSelector, find_matches
from .uia_impl import (
    MockUiaBackend,
    UiaBackend,
    UiaElementRecord,
    create_uia_backend,
    filter_records,
    uia_deps_available,
)

__all__ = ["UiaControlProvider", "UiaStubProvider", "MockUiaBackend"]


class UiaControlProvider(ControlProvider):
    """Windows desktop semantic control via UI Automation."""

    name = "uia"

    def __init__(
        self,
        *,
        display: str | None = None,
        session_id: str | None = None,
        backend: UiaBackend | None = None,
    ) -> None:
        self.display = display
        self.session_id = session_id
        self._backend = create_uia_backend(backend)
        self._cache: ControlSnapshot | None = None
        self._record_by_id: dict[str, UiaElementRecord] = {}

    def available(self) -> tuple[bool, str]:
        if isinstance(self._backend, MockUiaBackend):
            return True, "uia mock backend"
        return uia_deps_available()

    def _records_to_nodes(self, records: list[UiaElementRecord]) -> list[ControlNode]:
        nodes: list[ControlNode] = []
        self._record_by_id.clear()
        for record in records:
            node_id = f"uia:{record.key}"
            node = ControlNode(
                id=node_id,
                backend=self.name,
                role=record.role,
                name=record.name,
                bounds=record.bounds,
                app_label=record.app_label,
                window_id=record.window_id,
                window_title=record.window_title,
                provider_ref=record.provider_ref,
                state={"automation_id": record.automation_id, "uia_key": record.key},
            )
            nodes.append(node)
            self._record_by_id[node_id] = record
        return nodes

    def snapshot(
        self,
        *,
        window_id: str | None = None,
        app: str | None = None,
        max_depth: int = 8,
    ) -> ControlSnapshot:
        self._backend.connect()
        records = self._backend.collect_elements(app=app, window_id=window_id, max_depth=max_depth)
        nodes = self._records_to_nodes(records)
        snapshot = ControlSnapshot(
            backend=self.name,
            window_id=window_id,
            app_label=app,
            nodes={node.id: node for node in nodes},
            root_ids=[node.id for node in nodes[:20]],
        )
        self._cache = snapshot
        return snapshot

    def find(self, selector: ControlSelector) -> list[ControlNode]:
        snapshot = self._cache
        if snapshot is None or not snapshot.nodes:
            snapshot = self.snapshot(app=selector.app, window_id=selector.window_id)
        if snapshot.nodes:
            matches = find_matches(snapshot.nodes, selector)
            if matches:
                return matches
        self._backend.connect()
        records = filter_records(
            self._backend.collect_elements(app=selector.app, window_id=selector.window_id),
            selector,
        )
        nodes = self._records_to_nodes(records)
        for node in nodes:
            snapshot.nodes[node.id] = node
        self._cache = snapshot
        return nodes

    def _record_for(self, element_id: str) -> UiaElementRecord:
        record = self._record_by_id.get(element_id)
        if record is None:
            snapshot = self._cache or self.snapshot()
            node = snapshot.nodes.get(element_id)
            if node is None:
                raise VDisplayError(f"uia: unknown element {element_id}")
            key = str(node.state.get("uia_key") or element_id.removeprefix("uia:"))
            record = UiaElementRecord(
                key=key,
                name=node.name,
                role=node.role,
                bounds=node.bounds or ControlBounds(x=0, y=0, width=0, height=0),
                automation_id=node.state.get("automation_id"),
                provider_ref=node.provider_ref,
                raw=None,
            )
        return record

    def invoke(self, element_id: str, *, action: str | None = None) -> dict[str, Any]:
        try:
            record = self._record_for(element_id)
            self._backend.invoke(record)
            return {"ok": True, "element_id": element_id, "backend": self.name, "action": action, "method": "invoke"}
        except Exception as exc:
            return {"ok": False, "element_id": element_id, "backend": self.name, "reason": str(exc)}

    def focus(self, element_id: str) -> dict[str, Any]:
        try:
            record = self._record_for(element_id)
            self._backend.focus(record)
            return {"ok": True, "element_id": element_id, "backend": self.name, "method": "focus"}
        except Exception as exc:
            return {"ok": False, "element_id": element_id, "backend": self.name, "reason": str(exc)}

    def set_value(self, element_id: str, value: str) -> dict[str, Any]:
        try:
            record = self._record_for(element_id)
            self._backend.set_value(record, value)
            return {
                "ok": True,
                "element_id": element_id,
                "backend": self.name,
                "value": value,
                "method": "set_value",
            }
        except Exception as exc:
            return {
                "ok": False,
                "element_id": element_id,
                "backend": self.name,
                "value": value,
                "reason": str(exc),
            }

    def bounds(self, element_id: str) -> ControlBounds | None:
        snapshot = self._cache or self.snapshot()
        node = snapshot.nodes.get(element_id)
        if node is None:
            return None
        return node.bounds


UiaStubProvider = UiaControlProvider
