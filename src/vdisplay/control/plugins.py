"""Control provider plugin registration — in-process and entry-point loaders."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal

from .base import ControlProvider
from .descriptors import BUILTIN_PROVIDER_DESCRIPTORS, ProviderDescriptor
from .registry import ProviderFactory, ProviderRegistry, _BUILTIN_FACTORIES

logger = logging.getLogger(__name__)

PluginSource = Literal["builtin", "entrypoint", "manual"]

_REGISTRY: ProviderRegistry | None = None
_PLUGINS: dict[str, "RegisteredPlugin"] = {}


@dataclass(frozen=True)
class RegisteredPlugin:
    descriptor: ProviderDescriptor
    factory: ProviderFactory
    source: PluginSource
    entry_point: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = self.descriptor.to_dict()
        payload["source"] = self.source
        if self.entry_point:
            payload["entry_point"] = self.entry_point
        return payload


def _register_plugin(
    registry: ProviderRegistry,
    descriptor: ProviderDescriptor,
    factory: ProviderFactory,
    *,
    source: PluginSource,
    entry_point: str | None = None,
) -> None:
    registry.register(descriptor, factory)
    _PLUGINS[descriptor.provider_id] = RegisteredPlugin(
        descriptor=descriptor,
        factory=factory,
        source=source,
        entry_point=entry_point,
    )


def _bootstrap_builtin_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    for descriptor in BUILTIN_PROVIDER_DESCRIPTORS:
        factory = _BUILTIN_FACTORIES.get(descriptor.provider_id)
        if factory is None:
            continue
        _register_plugin(registry, descriptor, factory, source="builtin")
    return registry


def load_entry_point_plugins(registry: ProviderRegistry) -> list[str]:
    """Load plugins declared under ``vdisplay.control_providers`` entry-point group."""
    loaded: list[str] = []
    try:
        from importlib.metadata import entry_points
    except ImportError:
        return loaded

    try:
        eps = entry_points(group="vdisplay.control_providers")
    except TypeError:
        eps = entry_points().get("vdisplay.control_providers", [])

    for ep in eps:
        try:
            target = ep.load()
            if callable(target):
                target(registry)
                loaded.append(ep.name)
                continue
            if hasattr(target, "descriptor") and hasattr(target, "factory"):
                _register_plugin(
                    registry,
                    target.descriptor,
                    target.factory,
                    source="entrypoint",
                    entry_point=ep.name,
                )
                loaded.append(ep.name)
        except Exception:
            logger.exception("failed to load control plugin entry point %s", ep.name)
    return loaded


def get_provider_registry(*, reload: bool = False) -> ProviderRegistry:
    global _REGISTRY
    if _REGISTRY is None or reload:
        _PLUGINS.clear()
        _REGISTRY = _bootstrap_builtin_registry()
        load_entry_point_plugins(_REGISTRY)
    return _REGISTRY


def register_control_provider(
    descriptor: ProviderDescriptor,
    factory: ProviderFactory,
    *,
    source: PluginSource = "manual",
    entry_point: str | None = None,
) -> None:
    """Register an adapter at runtime (tests, host integrations, optional wheels)."""
    registry = get_provider_registry()
    _register_plugin(
        registry,
        descriptor,
        factory,
        source=source,
        entry_point=entry_point,
    )


def unregister_control_provider(provider_id: str) -> bool:
    """Remove a manually or entry-point registered provider (builtins cannot be removed)."""
    plugin = _PLUGINS.get(provider_id)
    if plugin is None or plugin.source == "builtin":
        return False
    _PLUGINS.pop(provider_id, None)
    registry = get_provider_registry()
    registry._descriptors.pop(provider_id, None)  # noqa: SLF001
    registry._factories.pop(provider_id, None)  # noqa: SLF001
    for alias in plugin.descriptor.aliases:
        registry._factories.pop(alias, None)  # noqa: SLF001
    return True


def list_control_plugins() -> list[dict[str, Any]]:
    get_provider_registry()
    return [item.to_dict() for item in _PLUGINS.values()]


def iter_provider_names() -> list[str]:
    return get_provider_registry().list_names()


def reset_control_plugins_for_tests() -> None:
    """Test helper — rebuild registry from builtins only."""
    global _REGISTRY
    _REGISTRY = None
    _PLUGINS.clear()
    get_provider_registry()


def get_registered_descriptor(provider_id: str) -> ProviderDescriptor | None:
    normalized = provider_id.strip().lower()
    plugin = _PLUGINS.get(normalized)
    if plugin is not None:
        return plugin.descriptor
    for item in BUILTIN_PROVIDER_DESCRIPTORS:
        if item.provider_id == normalized or normalized in item.aliases:
            return item
    return None
