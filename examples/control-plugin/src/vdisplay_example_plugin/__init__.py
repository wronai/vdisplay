"""vdisplay example control plugin — entry-point registration for PR-18."""

from __future__ import annotations

from typing import Any

from vdisplay.control.plugins import register_control_provider
from vdisplay.control.registry import ProviderRegistry

from .my_provider import ECHO_DESCRIPTOR, EchoControlProvider

__all__ = ["EchoControlProvider", "ECHO_DESCRIPTOR", "register_plugin"]


def _build_echo(*, display: str | None = None, session_id: str | None = None) -> EchoControlProvider:
    return EchoControlProvider(display=display, session_id=session_id)


def register_plugin(registry: ProviderRegistry | None = None, **_kwargs: Any) -> None:
    """Entry point: ``vdisplay.control_providers`` group → ``echo``."""
    _ = registry  # entry-point loader passes registry; global register uses same instance
    register_control_provider(
        ECHO_DESCRIPTOR,
        _build_echo,
        source="entrypoint",
        entry_point="echo",
    )
