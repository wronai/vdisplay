"""Control provider plugin registration (PR-12)."""

from __future__ import annotations

from typing import Any

import pytest

from vdisplay.control.base import ControlProvider
from vdisplay.control.capabilities import POINTER_FALLBACK
from vdisplay.control.descriptors import ProviderDescriptor
from vdisplay.control.models import ControlBounds, ControlNode, ControlSnapshot
from vdisplay.control.plugins import (
    list_control_plugins,
    register_control_provider,
    reset_control_plugins_for_tests,
    unregister_control_provider,
)
from vdisplay.control.registry import default_provider_registry
from vdisplay.control.selector import ControlSelector


class _StubPluginProvider(ControlProvider):
    name = "temp-plugin"

    def available(self) -> tuple[bool, str]:
        return True, "stub ready"

    def snapshot(self, **kwargs: Any) -> ControlSnapshot:
        return ControlSnapshot(
            backend=self.name,
            window_id=None,
            app_label=None,
            nodes={},
            root_ids=[],
        )

    def find(self, selector: ControlSelector) -> list[ControlNode]:
        return []

    def invoke(self, element_id: str, *, action: str | None = None) -> dict[str, Any]:
        return {"ok": True, "element_id": element_id}

    def focus(self, element_id: str) -> dict[str, Any]:
        return {"ok": True, "element_id": element_id}

    def set_value(self, element_id: str, value: str) -> dict[str, Any]:
        return {"ok": True, "element_id": element_id, "value": value}

    def bounds(self, element_id: str) -> ControlBounds | None:
        return None


@pytest.fixture(autouse=True)
def _reset_plugins() -> None:
    reset_control_plugins_for_tests()
    yield
    reset_control_plugins_for_tests()


def test_register_and_list_plugin() -> None:
    descriptor = ProviderDescriptor(
        provider_id="temp-plugin",
        adapter_kind="test_stub",
        environments=frozenset({"desktop"}),
        session_kind=None,
        capabilities=POINTER_FALLBACK,
        base_score=42,
    )

    register_control_provider(
        descriptor,
        lambda **kwargs: _StubPluginProvider(),
        source="manual",
    )

    plugins = list_control_plugins()
    assert any(item["provider_id"] == "temp-plugin" and item["source"] == "manual" for item in plugins)

    registry = default_provider_registry()
    assert "temp-plugin" in registry.list_names()
    provider = registry.build("temp-plugin")
    assert provider.name == "temp-plugin"


def test_unregister_manual_plugin() -> None:
    descriptor = ProviderDescriptor(
        provider_id="temp-plugin",
        adapter_kind="test_stub",
        environments=frozenset({"desktop"}),
        session_kind=None,
        capabilities=POINTER_FALLBACK,
    )
    register_control_provider(descriptor, lambda **kwargs: _StubPluginProvider())
    assert unregister_control_provider("temp-plugin") is True
    assert unregister_control_provider("atspi") is False
    assert "temp-plugin" not in default_provider_registry().list_names()


def test_extension_catalog_includes_plugins(agent_client) -> None:
    client, _runtime = agent_client
    payload = client.get("/diagnostics/control").json()
    assert payload["ok"] is True
    extensions = payload["data"]["extensions"]
    assert "plugins" in extensions
    assert len(extensions["plugins"]) >= 4
