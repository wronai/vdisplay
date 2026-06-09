from __future__ import annotations

import json
import urllib.error

import pytest

from vdisplay.agent_config import resolve_agent_url, use_agent
from vdisplay.client import AgentClient
from vdisplay.exceptions import VDisplayError


def test_use_agent_false_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VDISPLAY_AGENT_URL", raising=False)
    assert use_agent() is False
    assert resolve_agent_url() is None


def test_client_unreachable_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_AGENT_URL", "http://127.0.0.1:1")
    client = AgentClient("http://127.0.0.1:1", timeout=0.5)
    with pytest.raises(VDisplayError, match="unreachable"):
        client.health()
