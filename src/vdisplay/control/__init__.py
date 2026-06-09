"""Accessibility-first desktop control plane."""

from .engine import resolve_provider
from .models import ControlNode, ControlRole, ControlSnapshot, ElementCapabilities, EnvironmentKind
from .policy import ControlCapabilityContract, assess_control_capability
from .selector import ControlSelector, parse_selector, pick_match

__all__ = [
    "ControlCapabilityContract",
    "ControlNode",
    "ControlRole",
    "ElementCapabilities",
    "ControlSelector",
    "ControlSnapshot",
    "EnvironmentKind",
    "assess_control_capability",
    "parse_selector",
    "pick_match",
    "resolve_provider",
]
