from __future__ import annotations

import pytest

from vdisplay.control.providers.atspi import AtspiControlProvider
from vdisplay.exceptions import VDisplayError


_PROBE_RESULT: bool | None = None
_PROBE_REASON: str | None = None


def _probe_atspi_integration() -> tuple[bool, str]:
    global _PROBE_RESULT, _PROBE_REASON
    if _PROBE_RESULT is None:
        provider = AtspiControlProvider()
        _PROBE_RESULT, _PROBE_REASON = provider.probe_integration()
    return _PROBE_RESULT, _PROBE_REASON or "AT-SPI integration unavailable"


def _atspi_integration_ready() -> bool:
    return _probe_atspi_integration()[0]


@pytest.fixture
def atspi_provider() -> AtspiControlProvider:
    ok, reason = _probe_atspi_integration()
    if not ok:
        pytest.skip(f"AT-SPI integration unavailable: {reason}")
    return AtspiControlProvider()


@pytest.mark.skipif(not _atspi_integration_ready(), reason="AT-SPI integration unavailable in test environment")
def test_atspi_snapshot_lists_nodes(atspi_provider: AtspiControlProvider) -> None:
    snapshot = atspi_provider.snapshot(max_depth=3)
    assert snapshot.backend == "atspi"
    assert len(snapshot.nodes) > 0


@pytest.mark.skipif(not _atspi_integration_ready(), reason="AT-SPI integration unavailable in test environment")
def test_controls_list_cli_integration(atspi_provider: AtspiControlProvider) -> None:
    from vdisplay.application.services.control import controls_list

    try:
        payload = controls_list(backend="atspi", max_depth=2)
    except VDisplayError as exc:
        if "timeout" in str(exc).lower() or "dbind" in str(exc).lower():
            pytest.skip(f"AT-SPI bus unstable during controls_list: {exc}")
        raise
    assert payload["ok"] is True
    assert payload["count"] > 0
