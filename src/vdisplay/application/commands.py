"""Shared command model for CLI, DSL, REST, and agent client."""

from __future__ import annotations

from .models import ArtifactRef, CommandRequest, CommandResult
from .parsers import parse_agent_body, parse_agent_control_body, parse_dsl
from .verbs import COMMAND_VERBS, QUERY_VERBS, CommandVerb

__all__ = [
    "CommandRequest",
    "CommandResult",
    "ArtifactRef",
    "CommandVerb",
    "QUERY_VERBS",
    "COMMAND_VERBS",
    "parse_dsl",
    "parse_agent_body",
    "parse_agent_control_body",
]