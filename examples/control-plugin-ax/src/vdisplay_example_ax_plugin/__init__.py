"""vdisplay example AX control plugin — entry-point registration (PR-23)."""

from __future__ import annotations

from typing import Any

from vdisplay.control.plugins import register_control_provider
from vdisplay.control.registry import ProviderRegistry

from .provider import EXAMPLE_AX_DESCRIPTOR, ExampleAxProvider, build_example_ax

__all__ = ["ExampleAxProvider", "EXAMPLE_AX_DESCRIPTOR", "register_plugin"]


def register_plugin(registry: ProviderRegistry | None = None, **_kwargs: Any) -> None:
    """Entry point: ``vdisplay.control_providers`` group → ``example-ax``."""
    _ = registry
    register_control_provider(
        EXAMPLE_AX_DESCRIPTOR,
        build_example_ax,
        source="entrypoint",
        entry_point="example-ax",
    )
