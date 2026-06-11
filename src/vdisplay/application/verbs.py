"""Backward-compatible re-export — see ``application.commands.verbs``."""

from __future__ import annotations

from .commands.verbs import COMMAND_VERBS, QUERY_VERBS, CommandVerb

__all__ = ["CommandVerb", "QUERY_VERBS", "COMMAND_VERBS"]
