"""Agent monitor payloads include natural-language summaries."""

from __future__ import annotations

from typing import Any

import pytest

from vdisplay_agent.services import outputs as outputs_svc


def test_list_outputs_payload_enriches_monitor_nl(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_monitors = [
        {
            "name": "DP-1",
            "connected": True,
            "primary": True,
            "width": 1920,
            "height": 1080,
            "nl": "Primary monitor DP-1 (1920×1080). Visible apps: Firefox.",
        }
    ]

    def fake_list_outputs(
        display: str | None,
        *,
        enrich_nl: bool = True,
        apps_only: bool = False,
    ) -> list[dict[str, Any]]:
        assert enrich_nl is True
        return fake_monitors

    monkeypatch.setattr(outputs_svc, "list_outputs", fake_list_outputs)
    monkeypatch.setattr(outputs_svc, "resolve_host_display", lambda _display: ":0")

    payload = outputs_svc.list_outputs_payload(display=":0", include_all=True)

    assert payload["monitors"][0]["nl"].startswith("Primary monitor")
