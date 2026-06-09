"""Minimal example ControlProvider — echo stub for plugin author guide (PR-18)."""

from __future__ import annotations

from typing import Any

from vdisplay.control.base import ControlProvider
from vdisplay.control.capabilities import ProviderCapabilities
from vdisplay.control.descriptors import ProviderDescriptor
from vdisplay.control.models import ControlBounds, ControlNode, ControlRole, ControlSnapshot
from vdisplay.control.selector import ControlSelector
from vdisplay.control.verify_strategy import VerifyStrategy

ECHO_CAPABILITIES = ProviderCapabilities(
    can_invoke=True,
    can_focus=True,
    can_set_value=True,
    supports_semantic_verify=True,
)

ECHO_DESCRIPTOR = ProviderDescriptor(
    provider_id="echo",
    adapter_kind="example_echo",
    environments=frozenset({"desktop"}),
    session_kind=None,
    capabilities=ECHO_CAPABILITIES,
    actions=frozenset({"snapshot", "find", "invoke", "focus", "set_value", "bounds"}),
    verify_strategies=frozenset({VerifyStrategy.STRUCTURE}),
    required_deps=(),
    aliases=frozenset({"example-echo"}),
    base_score=35,
    cost=0.1,
    risk=0.05,
)


class EchoControlProvider(ControlProvider):
    """Returns synthetic nodes — useful for CI and plugin integration tests."""

    name = "echo"

    def __init__(self, *, display: str | None = None, session_id: str | None = None) -> None:
        self.display = display
        self.session_id = session_id
        self._nodes: dict[str, ControlNode] = {}

    def available(self) -> tuple[bool, str]:
        return True, "echo example plugin ready"

    def snapshot(
        self,
        *,
        window_id: str | None = None,
        app: str | None = None,
        max_depth: int = 8,
    ) -> ControlSnapshot:
        node_id = "echo:demo-button"
        node = ControlNode(
            id=node_id,
            backend=self.name,
            role=ControlRole.BUTTON,
            name="demo-button",
            bounds=ControlBounds(x=10, y=20, width=120, height=32),
            state={"example": True},
        )
        self._nodes = {node_id: node}
        return ControlSnapshot(
            backend=self.name,
            window_id=window_id,
            app_label=app,
            nodes=self._nodes,
            root_ids=[node_id],
        )

    def find(self, selector: ControlSelector) -> list[ControlNode]:
        snapshot = self.snapshot()
        if selector.name == "demo-button" or selector.name_contains == "demo":
            return [snapshot.nodes["echo:demo-button"]]
        return []

    def invoke(self, element_id: str, *, action: str | None = None) -> dict[str, Any]:
        return {"ok": True, "backend": self.name, "element_id": element_id, "action": action}

    def focus(self, element_id: str) -> dict[str, Any]:
        return {"ok": True, "backend": self.name, "element_id": element_id}

    def set_value(self, element_id: str, value: str) -> dict[str, Any]:
        return {"ok": True, "backend": self.name, "element_id": element_id, "value": value}

    def bounds(self, element_id: str) -> ControlBounds | None:
        node = self._nodes.get(element_id)
        return node.bounds if node is not None else None
