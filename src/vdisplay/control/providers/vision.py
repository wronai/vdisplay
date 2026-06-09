"""Vision-only surface provider stub — screenshot/OCR verify without semantic trees."""

from __future__ import annotations

from typing import Any

from ..base import ControlProvider
from ..models import ControlBounds, ControlNode, ControlRole, ControlSnapshot
from ..selector import ControlSelector, find_matches, pick_match


class VisionStubProvider(ControlProvider):
    """Stub adapter for canvas/game/stream surfaces; invoke paths deferred to PR-18+."""

    name = "vision"

    def __init__(self, *, display: str | None = None, session_id: str | None = None) -> None:
        self.display = display
        self.session_id = session_id
        self._cache: ControlSnapshot | None = None

    def available(self) -> tuple[bool, str]:
        return True, "vision stub (screenshot/OCR verify; semantic tree unavailable)"

    def snapshot(
        self,
        *,
        window_id: str | None = None,
        app: str | None = None,
        max_depth: int = 8,
    ) -> ControlSnapshot:
        snapshot = ControlSnapshot(
            backend=self.name,
            window_id=window_id,
            app_label=app,
            nodes={},
            root_ids=[],
        )
        self._cache = snapshot
        return snapshot

    def find(self, selector: ControlSelector) -> list[ControlNode]:
        snapshot = self._cache or self.snapshot()
        if selector.vision_anchor:
            node_id = f"vision:{selector.vision_anchor}"
            node = ControlNode(
                id=node_id,
                backend=self.name,
                role=ControlRole.UNKNOWN,
                name=selector.vision_anchor,
                bounds=ControlBounds(x=0, y=0, width=0, height=0),
                state={"stub": True, "anchor": selector.vision_anchor},
            )
            snapshot.nodes[node_id] = node
            snapshot.root_ids = [node_id]
            self._cache = snapshot
            return [node]
        return find_matches(snapshot.nodes.values(), selector)

    def invoke(self, element_id: str, *, action: str | None = None) -> dict[str, Any]:
        return {
            "ok": False,
            "stub": True,
            "element_id": element_id,
            "reason": "vision invoke not implemented — use screenshot verify",
        }

    def focus(self, element_id: str) -> dict[str, Any]:
        return {
            "ok": False,
            "stub": True,
            "element_id": element_id,
            "reason": "vision focus not implemented",
        }

    def set_value(self, element_id: str, value: str) -> dict[str, Any]:
        return {
            "ok": False,
            "stub": True,
            "element_id": element_id,
            "value": value,
            "reason": "vision set_value not implemented",
        }

    def bounds(self, element_id: str) -> ControlBounds | None:
        snapshot = self._cache or self.snapshot()
        node = snapshot.nodes.get(element_id)
        if node is None:
            return None
        return node.bounds
