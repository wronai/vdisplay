from __future__ import annotations

import pytest

from vdisplay.capture.portal_screencast import _screencast_multiple


def test_screencast_multiple_explicit() -> None:
    assert _screencast_multiple(True) is True
    assert _screencast_multiple(False) is False


def test_screencast_multiple_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VDISPLAY_SCREENCAST_MULTIPLE", raising=False)
    assert _screencast_multiple(None) is False
    monkeypatch.setenv("VDISPLAY_SCREENCAST_MULTIPLE", "1")
    assert _screencast_multiple(None) is True
    monkeypatch.setenv("VDISPLAY_SCREENCAST_MULTIPLE", "yes")
    assert _screencast_multiple(None) is True
