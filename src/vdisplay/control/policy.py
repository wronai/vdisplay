"""Control capability assessment and provider routing policy."""

from __future__ import annotations

import os
import shutil
from dataclasses import asdict, dataclass, field
from typing import Any

from ..discovery import resolve_host_display


@dataclass(frozen=True)
class ControlCapabilityContract:
    supports_semantic_control: bool
    supports_unattended_control: bool
    supports_invoke: bool
    supports_set_value: bool
    supports_focus: bool
    requires_accessibility_enablement: bool
    fallback_to_pointer_injection: bool
    backends: list[str]
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _atspi_ready() -> tuple[bool, str]:
    try:
        from .providers.atspi import AtspiControlProvider

        return AtspiControlProvider().available()
    except Exception as exc:
        return False, str(exc)


def _xdotool_ready() -> tuple[bool, str]:
    if shutil.which("xdotool"):
        return True, "xdotool available"
    return False, "xdotool not installed"


def _terminal_ready() -> tuple[bool, str]:
    try:
        from .providers.terminal import TerminalControlProvider

        return TerminalControlProvider().available()
    except Exception as exc:
        return False, str(exc)


def assess_control_capability(*, display: str | None = None) -> ControlCapabilityContract:
    reasons: list[str] = []
    backends: list[str] = []

    atspi_ok, atspi_reason = _atspi_ready()
    xdotool_ok, xdotool_reason = _xdotool_ready()
    terminal_ok, terminal_reason = _terminal_ready()

    if atspi_ok:
        backends.append("atspi")
        reasons.append(atspi_reason)
    else:
        reasons.append(f"atspi unavailable: {atspi_reason}")

    if xdotool_ok:
        backends.append("x11-fallback")
        reasons.append(xdotool_reason)

    if terminal_ok:
        backends.append("terminal")
        reasons.append(terminal_reason)
    else:
        reasons.append(f"terminal unavailable: {terminal_reason}")

    gtk_a11y = os.environ.get("GTK_A11Y", "")
    qt_a11y = os.environ.get("QT_ACCESSIBILITY", "")
    if gtk_a11y:
        reasons.append(f"GTK_A11Y={gtk_a11y}")
    if qt_a11y:
        reasons.append(f"QT_ACCESSIBILITY={qt_a11y}")

    resolve_host_display(display or os.environ.get("DISPLAY"))

    return ControlCapabilityContract(
        supports_semantic_control=atspi_ok,
        supports_unattended_control=atspi_ok,
        supports_invoke=atspi_ok or xdotool_ok or terminal_ok,
        supports_set_value=atspi_ok or xdotool_ok or terminal_ok,
        supports_focus=atspi_ok or xdotool_ok or terminal_ok,
        requires_accessibility_enablement=not atspi_ok,
        fallback_to_pointer_injection=xdotool_ok,
        backends=backends,
        reasons=reasons,
    )
