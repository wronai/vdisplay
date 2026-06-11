"""Backward-compatible re-export — see ``application.commands.parsers``."""

from __future__ import annotations

from .commands.parsers import parse_agent_body, parse_agent_control_body, parse_dsl

__all__ = ["parse_dsl", "parse_agent_body", "parse_agent_control_body"]
