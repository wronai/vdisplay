"""Agent task persistence (PR-11)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest


@pytest.fixture
def agent_client_with_db(tmp_path, monkeypatch: pytest.MonkeyPatch):
    pytest.importorskip("sqlmodel")
    pytest.importorskip("fastapi")
    db_path = tmp_path / "agent-tasks.db"
    monkeypatch.setenv("VDISPLAY_AGENT_DB", str(db_path))

    from fastapi.testclient import TestClient
    from vdisplay_agent.runtime import AgentRuntime
    from vdisplay_agent.server import create_app

    runtime = AgentRuntime()
    app = create_app(runtime)
    with TestClient(app) as client:
        yield client, runtime, db_path


def test_startup_marks_orphan_tasks_stale(agent_client_with_db) -> None:
    client, runtime, db_path = agent_client_with_db
    from vdisplay_agent.task_store import TaskStatus, TaskStore

    old_store = TaskStore(db_path)
    old_store.create_task(
        task_id="sampler-orphan",
        kind="capture_sampler",
        broker_id="dead-broker",
        status=TaskStatus.RUNNING,
        config={"mode": "desktop"},
    )

    runtime2 = __import__("vdisplay_agent.runtime", fromlist=["AgentRuntime"]).AgentRuntime(
        task_store=TaskStore(db_path),
        broker_id="new-broker",
    )
    from vdisplay_agent.server import create_app

    with __import__("fastapi.testclient", fromlist=["TestClient"]).TestClient(create_app(runtime2)) as client2:
        row = runtime2.task_store.get_task("sampler-orphan")
        assert row is not None
        assert row.status == TaskStatus.STALE


def test_sampler_creates_persisted_task(agent_client_with_db, tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    client, runtime, _db_path = agent_client_with_db
    out_dir = tmp_path / "sampler-out"

    def fake_capture(output, **kwargs):
        path = Path(output)
        path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 200)
        return {"path": str(path), "bytes": path.stat().st_size, "method": "portal-screencast"}

    monkeypatch.setattr("vdisplay_agent.services.sampler.capture_host_to_file", fake_capture)
    monkeypatch.setattr(
        "vdisplay.application.services.sampler_loop.assess_unattended_capture",
        lambda **kwargs: type(
            "C",
            (),
            {
                "supports_unattended_capture": True,
                "requires_user_consent": False,
                "to_dict": lambda self: {"supports_unattended_capture": True},
            },
        )(),
    )

    started = client.post(
        "/sampler/start",
        json={"interval_s": 0.1, "mode": "desktop", "out_dir": str(out_dir), "max_frames": 1, "format": "png"},
    ).json()
    assert started["ok"] is True
    task_id = started["data"]["task_id"]
    assert task_id

    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        status = client.get("/sampler/status").json()
        if int(status["data"].get("frames_saved") or 0) >= 1 or not status["data"].get("running"):
            break
        time.sleep(0.05)

    listed = client.get("/tasks").json()
    assert listed["ok"] is True
    tasks = listed["data"]["tasks"]
    assert any(item["task_id"] == task_id for item in tasks)
    assert any(item["status"] == "running" for item in tasks if item["task_id"] == task_id)

    detail = client.get(f"/tasks/{task_id}").json()
    assert detail["ok"] is True
    assert detail["data"]["kind"] == "capture_sampler"
    assert detail["data"]["config"]["mode"] == "desktop"

    heartbeat = client.post(f"/tasks/{task_id}/heartbeat", json={"state": {"ping": True}}).json()
    assert heartbeat["ok"] is True
    assert heartbeat["data"]["state"]["ping"] is True

    stopped = client.post("/sampler/stop").json()
    assert stopped["ok"] is True

    row = runtime.task_store.get_task(task_id)
    assert row is not None
    assert row.status == "stopped"


def test_virtual_session_registers_task(agent_client_with_db) -> None:
    client, runtime, _db_path = agent_client_with_db
    started = client.post("/session/virtual/start", json={"width": 640, "height": 480, "display": ":99"}).json()
    assert started["ok"] is True
    session_id = started["data"]["session_id"]

    row = runtime.task_store.get_task(session_id)
    assert row is not None
    assert row.kind == "virtual"
    assert row.status == "running"

    stopped = client.post(f"/session/{session_id}/stop").json()
    assert stopped["ok"] is True
    row = runtime.task_store.get_task(session_id)
    assert row is not None
    assert row.status == "stopped"


def test_task_store_recovers_corrupt_db(tmp_path: Path) -> None:
    pytest.importorskip("sqlmodel")
    from vdisplay_agent.task_store import TaskStore, recover_corrupt_task_db

    db_path = tmp_path / "agent-tasks.db"
    db_path.write_text("Traceback (most recent call last):\n", encoding="utf-8")
    backup = recover_corrupt_task_db(db_path)
    assert backup is not None
    assert not db_path.is_file()

    store = TaskStore(db_path)
    store.create_task(task_id="t1", kind="screencast", broker_id="b1")
    assert store.get_task("t1") is not None


def test_task_store_recovers_corrupt_db_during_update(tmp_path: Path) -> None:
    pytest.importorskip("sqlmodel")
    from vdisplay_agent.task_store import TaskStatus, TaskStore

    db_path = tmp_path / "agent-tasks.db"
    store = TaskStore(db_path)
    store.create_task(task_id="screencast:active", kind="screencast", broker_id="b1")

    db_path.write_text("Traceback (most recent call last):\n", encoding="utf-8")
    updated = store.update_task("screencast:active", status=TaskStatus.STOPPED, heartbeat=True)
    assert updated is None
    assert store.get_task("screencast:active") is None
