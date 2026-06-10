"""Projection read models for backend scores and map health."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vdisplay.application.events import (
    DomainEvent,
    command_completed,
    command_received,
    gui_map_built,
    gui_map_drift_detected,
)
from vdisplay.application.commands import CommandRequest, CommandResult, CommandVerb
from vdisplay.application.projections import (
    build_backend_scores,
    build_map_health,
    merge_backend_scores,
    refresh_projections,
)
from vdisplay.application.projections.backend_scores import provider_score_prior
from vdisplay.control.scoring import rank_providers
from vdisplay.control.selector import ControlSelector


def test_build_map_health_from_gui_map_events() -> None:
    events = [
        gui_map_built(
            session_id="sess",
            request_id="r1",
            map_path="/tmp/chat.map.json",
            element_count=12,
            region_count=1,
            scope_ids=["chat"],
        ),
        gui_map_drift_detected(
            session_id="sess",
            request_id="r2",
            map_path="/tmp/chat.map.json",
            scope_id="chat",
            drifted=True,
            recommendation="refresh_required",
            actionable=True,
            summary={"missing": 1, "bounds": 0},
        ),
    ]
    health = build_map_health(events)
    entry = health["by_map_path"]["/tmp/chat.map.json"]
    assert entry["element_count"] == 12
    assert entry["drift_count"] == 1
    assert entry["refresh_required"] is True
    assert entry["scopes"]["chat"]["missing"] == 1


def test_build_map_health_from_step_diagnostics() -> None:
    events = [
        DomainEvent(
            event_id="1",
            event_type="StepRecorded",
            occurred_at_ms=100,
            session_id="sess",
            request_id="r1",
            aggregate="command",
            body={
                "ok": True,
                "diagnostics": {
                    "control": {
                        "map": {"path": "/maps/app.json", "scope": "main"},
                        "verify": {
                            "map_drift": {
                                "drifted": True,
                                "recommendation": "stable_with_cosmetic_drift",
                                "summary": {"bounds": 2},
                            }
                        },
                    }
                },
            },
        )
    ]
    health = build_map_health(events)
    entry = health["by_map_path"]["/maps/app.json"]
    assert entry["drift_count"] == 1
    assert entry["scopes"]["main"]["bounds"] == 2


def test_merge_backend_scores_accumulates() -> None:
    merged = merge_backend_scores(
        {"default": {"atspi": {"success": 2, "fail": 0, "score": 100}}},
        {"default": {"atspi": {"success": 1, "fail": 1, "score": 50}}},
    )
    bucket = merged["default"]["atspi"]
    assert bucket["success"] == 3
    assert bucket["fail"] == 1
    assert bucket["score"] == 75


def test_provider_score_prior_boosts_reliable_backend() -> None:
    scores = {"default": {"vision": {"success": 9, "fail": 1, "score": 90}}}
    boost, reasons = provider_score_prior("vision", application_profile="default", scores=scores)
    assert boost > 0
    assert any("backend score prior" in reason for reason in reasons)


def test_rank_providers_applies_backend_score_prior(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "vdisplay.application.projections.backend_scores.load_merged_backend_scores",
        lambda **kwargs: {
            "default": {
                "atspi": {"success": 10, "fail": 0, "score": 100},
                "x11": {"success": 1, "fail": 9, "score": 10},
            }
        },
    )
    monkeypatch.setattr(
        "vdisplay.control.scoring._atspi_ready",
        lambda: (True, "atspi ok"),
    )
    monkeypatch.setattr(
        "vdisplay.control.scoring._xdotool_ready",
        lambda: (True, "xdotool ok"),
    )
    from vdisplay.control.scoring import _x11_linux_eligibility

    monkeypatch.setattr(
        "vdisplay.control.scoring._x11_linux_eligibility",
        lambda host, display: (True, ["x11 ok"], []),
    )
    monkeypatch.setattr(
        "vdisplay.control.scoring._x11_invoke_capabilities",
        lambda eligible=True, display=None: (True, ["invoke"], [], True, True),
    )

    ranked, _ = rank_providers(selector=ControlSelector(role="button"))
    atspi = next(item for item in ranked if item.provider == "atspi")
    x11 = next(item for item in ranked if item.provider == "x11")
    assert atspi.score > x11.score
    assert any("backend score prior" in reason for reason in atspi.reasons)


def test_refresh_projections_writes_map_health(tmp_path: Path) -> None:
    events = [
        gui_map_built(
            session_id="demo",
            request_id=None,
            map_path=str(tmp_path / "map.json"),
            element_count=3,
        )
    ]
    index = tmp_path / "index.jsonl"
    index.write_text(
        "\n".join(json.dumps(event.to_dict(), ensure_ascii=False) for event in events) + "\n",
        encoding="utf-8",
    )
    refresh_projections(tmp_path)
    assert (tmp_path / "projections" / "map_health.json").is_file()
    payload = json.loads((tmp_path / "projections" / "map_health.json").read_text(encoding="utf-8"))
    assert payload["by_map_path"]


def test_backend_scores_from_control_action_planned() -> None:
    events = [
        DomainEvent(
            event_id="1",
            event_type="ControlActionPlanned",
            occurred_at_ms=1,
            session_id="s",
            request_id="r",
            aggregate="control_action",
            body={
                "routing": {
                    "selected_provider": "atspi",
                    "application_profile": "native_gtk",
                }
            },
        )
    ]
    scores = build_backend_scores(events)
    assert "native_gtk" not in scores or scores["native_gtk"]["atspi"]["success"] == 0


def test_backend_scores_from_verification_event() -> None:
    events = [
        command_received(
            CommandRequest(verb=CommandVerb.CONTROL_CLICK, request_id="r1", session_id="s1"),
            route="local",
        ),
        command_completed(
            CommandRequest(verb=CommandVerb.CONTROL_CLICK, request_id="r1", session_id="s1"),
            CommandResult.success(
                action="control_click",
                data={},
                diagnostics={
                    "control": {
                        "routing": {"selected_provider": "atspi", "application_profile": "default"},
                        "verify": {"verified": True},
                    }
                },
            ),
            route="local",
            duration_ms=5,
        ),
    ]
    scores = build_backend_scores(events)
    assert scores["default"]["atspi"]["success"] >= 1
