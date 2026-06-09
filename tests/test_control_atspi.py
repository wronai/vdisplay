from __future__ import annotations

import pytest

from vdisplay.control.providers.atspi import AtspiControlProvider


def _atspi_available() -> bool:
    provider = AtspiControlProvider()
    ok, _ = provider.available()
    return ok


@pytest.mark.skipif(not _atspi_available(), reason="AT-SPI unavailable in test environment")
def test_atspi_snapshot_lists_nodes() -> None:
    provider = AtspiControlProvider()
    snapshot = provider.snapshot(max_depth=3)
    assert snapshot.backend == "atspi"
    assert len(snapshot.nodes) > 0
    assert len(snapshot.nodes) > 0


@pytest.mark.skipif(not _atspi_available(), reason="AT-SPI unavailable in test environment")
def test_controls_list_cli_integration() -> None:
    from vdisplay.application.services.control import controls_list

    payload = controls_list(backend="atspi", max_depth=2)
    assert payload["ok"] is True
    assert payload["count"] > 0
