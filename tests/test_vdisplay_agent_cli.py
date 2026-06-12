"""vdisplay-agent CLI defaults."""

from __future__ import annotations

import pytest

from vdisplay_agent.cli import _default_serve_port


def test_default_serve_port_from_agent_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VDISPLAY_AGENT_PORT", raising=False)
    monkeypatch.setenv("VDISPLAY_AGENT_URL", "http://127.0.0.1:8766")
    assert _default_serve_port() == 8766


def test_default_serve_port_prefers_agent_url_over_port_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_AGENT_PORT", "8765")
    monkeypatch.setenv("VDISPLAY_AGENT_URL", "http://127.0.0.1:8766")
    assert _default_serve_port() == 8766


def test_default_serve_port_uses_port_env_when_url_has_no_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_AGENT_PORT", "8777")
    monkeypatch.setenv("VDISPLAY_AGENT_URL", "http://127.0.0.1")
    assert _default_serve_port() == 8777
