from __future__ import annotations

import pytest

from vdisplay_agent.serve_port import (
    _parse_ss_pids,
    ensure_broker_port_free,
    find_listener_pids,
    stop_pids,
)


def test_parse_ss_pids() -> None:
    output = 'LISTEN 0 128 127.0.0.1:8765 users:(("python3",pid=12345,fd=3))'
    assert _parse_ss_pids(output) == [12345]


def test_ensure_broker_port_free_no_listeners(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("vdisplay_agent.serve_port.find_listener_pids", lambda port: [])
    ensure_broker_port_free("127.0.0.1", 8765)


def test_ensure_broker_port_free_stops_vdisplay_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stopped: list[int] = []

    monkeypatch.setattr("vdisplay_agent.serve_port.find_listener_pids", lambda port: [4242])
    monkeypatch.setattr("vdisplay_agent.serve_port._probe_is_vdisplay_agent", lambda h, p: True)
    monkeypatch.setattr(
        "vdisplay_agent.serve_port.stop_pids",
        lambda pids, *, host, port: stopped.extend(list(pids)) or list(pids),
    )

    ensure_broker_port_free("127.0.0.1", 8765)
    assert stopped == [4242]


def test_ensure_broker_port_free_rejects_foreign_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("vdisplay_agent.serve_port.find_listener_pids", lambda port: [9999])
    monkeypatch.setattr("vdisplay_agent.serve_port._probe_is_vdisplay_agent", lambda h, p: False)

    with pytest.raises(RuntimeError, match="already in use"):
        ensure_broker_port_free("127.0.0.1", 8765)


def test_find_listener_pids_excludes_current_pid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("vdisplay_agent.serve_port._pids_from_ss", lambda port: [111, 222])
    monkeypatch.setattr("vdisplay_agent.serve_port.os.getpid", lambda: 111)
    assert find_listener_pids(8765) == [222]


def test_stop_pids_ignores_current_pid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("vdisplay_agent.serve_port.os.getpid", lambda: 50)
    killed: list[tuple[int, int]] = []

    def fake_kill(pid: int, sig: int) -> None:
        killed.append((pid, sig))

    monkeypatch.setattr("vdisplay_agent.serve_port.os.kill", fake_kill)
    monkeypatch.setattr("vdisplay_agent.serve_port._pid_alive", lambda pid: False)

    assert stop_pids([50, 51], host="127.0.0.1", port=8765) == [51]
    assert killed == [(51, 15)]
