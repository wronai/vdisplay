from __future__ import annotations

from vdisplay.application.commands import CommandRequest, CommandVerb
from vdisplay.control.contracts import (
    control_route_request_from_command,
    provider_score_from_dataclass,
)
from vdisplay.control.scoring import ProviderScore, score_to_confidence


def test_provider_score_contract_maps_confidence() -> None:
    score = ProviderScore(provider="browser", score=270, eligible=True, reasons=["dom"])
    contract = provider_score_from_dataclass(score)
    assert contract.provider == "browser"
    assert contract.confidence == score_to_confidence(270, eligible=True)
    score_visual = ProviderScore(
        provider="browser",
        score=270,
        eligible=True,
        supports_visual_verify=True,
    )
    assert provider_score_from_dataclass(score_visual).supports_verify_visual is True


def test_control_route_request_from_command() -> None:
    cmd = CommandRequest(
        verb=CommandVerb.CONTROL_CLICK,
        control_backend="auto",
        control_role="button",
        control_name="OK",
        control_environment="browser",
        control_verify=True,
        control_screenshot_verify=True,
        line="CONTROL_CLICK",
    )
    request = control_route_request_from_command(cmd)
    assert request.verify_semantic is True
    assert request.verify_screenshot is True
    assert request.selector.role == "button"
    assert request.selector.environment == "browser"
