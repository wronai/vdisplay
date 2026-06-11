from __future__ import annotations

import time

import pytest

from vdisplay.exceptions import VDisplayError


def test_screencast_recovery_respects_cooldown(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay_agent.services import screencast_recovery as mod
    from vdisplay_agent.session_store import SessionStore

    monkeypatch.setattr(mod, "_recovery_cooldown_s", lambda: 60.0)
    mod._LAST_RECOVERY_ATTEMPT_MONO = time.monotonic()

    store = SessionStore()
    calls: list[bool] = []

    def fake_start(*args, **kwargs):
        calls.append(kwargs.get("interactive", True))
        return {"ok": True, "ready": True, "active": True}

    monkeypatch.setattr("vdisplay_agent.services.sessions.start_screencast", fake_start)

    assert mod.try_recover_screencast(store) is False
    assert calls == []

    mod._LAST_RECOVERY_ATTEMPT_MONO = 0.0
    assert mod.try_recover_screencast(store) is True
    assert calls == [False]


def test_web_frame_cache_skips_recovery(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay_agent.runtime import AgentRuntime
    from vdisplay_agent.services import web_frame_cache as mod

    runtime = AgentRuntime()
    runtime.store.screencast = None

    with pytest.raises(VDisplayError, match="screencast not ready"):
        mod.capture_monitor_frame_with_meta(runtime, "DP-1", use_cache=False)
