"""vdisplay example UIA control plugin — entry-point registration (PR-23)."""

from __future__ import annotations

from typing import Any

from vdisplay.control.plugins import register_control_provider
from vdisplay.control.registry import ProviderRegistry

from .provider import EXAMPLE_UIA_DESCRIPTOR, ExampleUiaProvider, build_example_uia

__all__ = ["ExampleUiaProvider", "EXAMPLE_UIA_DESCRIPTOR", "register_plugin"]


def register_plugin(registry: ProviderRegistry | None = None, **_kwargs: Any) -> None:
    """Entry point: ``vdisplay.control_providers`` group → ``example-uia``."""
    _ = registry
    register_control_provider(
        EXAMPLE_UIA_DESCRIPTOR,
        build_example_uia,
        source="entrypoint",
        entry_point="example-uia",
    )
