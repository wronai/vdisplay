"""SQLite persistence for long-running broker tasks (PR-11)."""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any

from sqlalchemy.exc import DatabaseError as SQLAlchemyDatabaseError
from sqlmodel import Field, Session, SQLModel, create_engine, select

_LOG = logging.getLogger(__name__)
_SENTINEL = object()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    STALE = "stale"


class AgentTask(SQLModel, table=True):
    task_id: str = Field(primary_key=True)
    kind: str
    status: str = TaskStatus.PENDING
    config_json: str = "{}"
    state_json: str = "{}"
    session_id: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    last_heartbeat_at: datetime | None = None
    broker_id: str = ""
    error: str | None = None


def default_task_db_path() -> Path:
    override = os.environ.get("VDISPLAY_AGENT_DB")
    if override:
        path = Path(override).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    cache_root = os.environ.get("XDG_CACHE_HOME")
    base = Path(cache_root).expanduser() if cache_root else Path.home() / ".cache"
    path = base / "vdisplay" / "agent-tasks.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _sqlite_db_valid(path: Path) -> bool:
    if not path.is_file():
        return True
    if path.stat().st_size < 16:
        return False
    try:
        with path.open("rb") as fh:
            if fh.read(16) != b"SQLite format 3\x00":
                return False
    except OSError:
        return False
    try:
        conn = sqlite3.connect(str(path))
        try:
            conn.execute("SELECT 1 FROM sqlite_master LIMIT 1")
        finally:
            conn.close()
        return True
    except sqlite3.DatabaseError:
        return False


def recover_corrupt_task_db(path: Path) -> Path | None:
    """Move a corrupt agent-tasks.db aside so a fresh database can be created."""
    if not path.is_file() or _sqlite_db_valid(path):
        return None
    backup = path.with_name(f"{path.name}.corrupt.{int(time.time())}")
    try:
        path.rename(backup)
    except OSError:
        try:
            path.unlink(missing_ok=True)
            backup = None
        except OSError:
            raise
    _LOG.warning("recovered corrupt agent task database (%s)", path)
    return backup


def task_to_dict(task: AgentTask) -> dict[str, Any]:
    return {
        "task_id": task.task_id,
        "kind": task.kind,
        "status": task.status,
        "session_id": task.session_id,
        "config": json.loads(task.config_json or "{}"),
        "state": json.loads(task.state_json or "{}"),
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
        "last_heartbeat_at": task.last_heartbeat_at.isoformat() if task.last_heartbeat_at else None,
        "broker_id": task.broker_id,
        "error": task.error,
    }


class TaskStore:
    """Thin repository over agent-tasks.db."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        path = Path(db_path).expanduser() if db_path else default_task_db_path()
        recover_corrupt_task_db(path)
        self.db_path = path
        self.engine = create_engine(
            f"sqlite:///{path}",
            connect_args={"check_same_thread": False},
        )
        SQLModel.metadata.create_all(self.engine)

    @staticmethod
    def _is_db_corrupt(exc: BaseException) -> bool:
        current: BaseException | None = exc
        while current is not None:
            if isinstance(current, (sqlite3.DatabaseError, SQLAlchemyDatabaseError)):
                return True
            message = str(current).lower()
            if "file is not a database" in message or "database disk image is malformed" in message:
                return True
            current = current.__cause__ or current.__context__
        return False

    def _run_with_recovery(self, fn, *, default: Any = _SENTINEL):
        try:
            return fn()
        except Exception as exc:
            if not self._is_db_corrupt(exc):
                raise
            _LOG.warning("agent task database error; recreating store: %s", exc)
            try:
                self._reopen_after_corruption()
                return fn()
            except Exception as retry_exc:
                if not self._is_db_corrupt(retry_exc):
                    raise
                _LOG.warning("agent task database still failing after recovery: %s", retry_exc)
                if default is not _SENTINEL:
                    return default
                raise

    def _reopen_after_corruption(self) -> None:
        try:
            self.engine.dispose()
        except Exception:
            pass
        recover_corrupt_task_db(self.db_path)
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            connect_args={"check_same_thread": False},
        )
        SQLModel.metadata.create_all(self.engine)

    def create_task(
        self,
        *,
        task_id: str,
        kind: str,
        broker_id: str,
        status: TaskStatus = TaskStatus.RUNNING,
        config: dict[str, Any] | None = None,
        state: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> AgentTask:
        def _create() -> AgentTask:
            now = _utcnow()
            task = AgentTask(
                task_id=task_id,
                kind=kind,
                status=str(status),
                config_json=json.dumps(config or {}),
                state_json=json.dumps(state or {}),
                session_id=session_id,
                created_at=now,
                updated_at=now,
                last_heartbeat_at=now,
                broker_id=broker_id,
            )
            with Session(self.engine) as session:
                session.add(task)
                session.commit()
                session.refresh(task)
            return task

        return self._run_with_recovery(_create)

    def get_task(self, task_id: str) -> AgentTask | None:
        def _get() -> AgentTask | None:
            with Session(self.engine) as session:
                return session.get(AgentTask, task_id)

        return self._run_with_recovery(_get, default=None)

    def list_tasks(
        self,
        *,
        status: str | None = None,
        kind: str | None = None,
    ) -> list[AgentTask]:
        def _list() -> list[AgentTask]:
            with Session(self.engine) as session:
                statement = select(AgentTask)
                if status:
                    statement = statement.where(AgentTask.status == status)
                if kind:
                    statement = statement.where(AgentTask.kind == kind)
                statement = statement.order_by(AgentTask.updated_at.desc())
                return list(session.exec(statement).all())

        return self._run_with_recovery(_list, default=[])

    def update_task(
        self,
        task_id: str,
        *,
        status: TaskStatus | str | None = None,
        state: dict[str, Any] | None = None,
        config: dict[str, Any] | None = None,
        error: str | None = None,
        heartbeat: bool = False,
    ) -> AgentTask | None:
        def _update() -> AgentTask | None:
            with Session(self.engine) as session:
                task = session.get(AgentTask, task_id)
                if task is None:
                    return None
                now = _utcnow()
                task.updated_at = now
                if status is not None:
                    task.status = str(status)
                if state is not None:
                    task.state_json = json.dumps(state)
                if config is not None:
                    task.config_json = json.dumps(config)
                if error is not None:
                    task.error = error
                if heartbeat:
                    task.last_heartbeat_at = now
                session.add(task)
                session.commit()
                session.refresh(task)
                return task

        return self._run_with_recovery(_update, default=None)

    def heartbeat(
        self,
        task_id: str,
        *,
        broker_id: str,
        state: dict[str, Any] | None = None,
    ) -> AgentTask | None:
        task = self.get_task(task_id)
        if task is None:
            return None
        if task.broker_id and task.broker_id != broker_id:
            return self.update_task(
                task_id,
                status=TaskStatus.STALE,
                error=f"heartbeat from foreign broker {broker_id}",
            )
        return self.update_task(task_id, state=state, heartbeat=True)

    def mark_orphan_running_as_stale(self, broker_id: str) -> int:
        """Tasks left running by a previous broker process."""
        def _mark() -> int:
            count = 0
            with Session(self.engine) as session:
                rows = session.exec(
                    select(AgentTask).where(AgentTask.status == TaskStatus.RUNNING)
                ).all()
                now = _utcnow()
                for task in rows:
                    if task.broker_id == broker_id:
                        continue
                    task.status = TaskStatus.STALE
                    task.error = "broker restarted — task not resumed"
                    task.updated_at = now
                    session.add(task)
                    count += 1
                session.commit()
            return count

        return self._run_with_recovery(_mark, default=0)
