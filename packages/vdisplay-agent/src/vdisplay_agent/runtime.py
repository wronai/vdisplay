"""AgentRuntime facade — delegates to broker services."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from .services import capabilities, capture, control, outputs, relay, sampler, sessions, tasks, windows
from .session_store import SessionRecord, SessionStore
from .task_store import TaskStore

__all__ = ["AgentRuntime", "SessionRecord", "SessionStore", "TaskStore"]


@dataclass
class AgentRuntime:
    """Privileged runtime: owns session store and broker services."""

    store: SessionStore = field(default_factory=SessionStore)
    task_store: TaskStore = field(default_factory=TaskStore)
    broker_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])

    @property
    def sessions(self) -> dict[str, SessionRecord]:
        return self.store.sessions

    @property
    def relay(self):
        return self.store.relay

    def platform_capabilities(self) -> dict[str, Any]:
        return capabilities.platform_capabilities()

    def diagnostics(self, *, display: str | None = None) -> dict[str, Any]:
        return capabilities.diagnostics(self.store, display=display)

    def outputs(self, *, display: str | None = None, include_all: bool = True) -> dict[str, Any]:
        return outputs.list_outputs_payload(display=display, include_all=include_all)

    def list_windows(self, **filters: Any) -> dict[str, Any]:
        return windows.list_windows(**filters)

    def start_virtual(self, **kwargs: Any) -> dict[str, Any]:
        return sessions.start_virtual(self.store, **kwargs, task_store=self.task_store, broker_id=self.broker_id)

    def start_mirror(self, **kwargs: Any) -> dict[str, Any]:
        return sessions.start_mirror(self.store, **kwargs, task_store=self.task_store, broker_id=self.broker_id)

    def start_relay(self, **kwargs: Any) -> dict[str, Any]:
        return sessions.start_relay(self.store, **kwargs, task_store=self.task_store, broker_id=self.broker_id)

    def start_terminal(self, **kwargs: Any) -> dict[str, Any]:
        return sessions.start_terminal(self.store, **kwargs, task_store=self.task_store, broker_id=self.broker_id)

    def start_browser(self, **kwargs: Any) -> dict[str, Any]:
        return sessions.start_browser(self.store, **kwargs, task_store=self.task_store, broker_id=self.broker_id)

    def start_screencast(self, **kwargs: Any) -> dict[str, Any]:
        return sessions.start_screencast(
            self.store,
            **kwargs,
            task_store=self.task_store,
            broker_id=self.broker_id,
        )

    def stop_screencast(self) -> dict[str, Any]:
        return sessions.stop_screencast(self.store, task_store=self.task_store)

    def screencast_status(self) -> dict[str, Any]:
        return sessions.screencast_status(self.store)

    def stop_session(self, session_id: str) -> dict[str, Any]:
        return sessions.stop_session(self.store, session_id, task_store=self.task_store)

    def recover_tasks(self) -> dict[str, Any]:
        return tasks.recover_on_startup(self.task_store, self.broker_id)

    def list_tasks(self, *, status: str | None = None, kind: str | None = None) -> dict[str, Any]:
        return tasks.list_tasks(self.task_store, status=status, kind=kind)

    def get_task(self, task_id: str) -> dict[str, Any]:
        return tasks.get_task(self.task_store, task_id)

    def heartbeat_task(self, task_id: str, *, state: dict[str, Any] | None = None) -> dict[str, Any]:
        return tasks.heartbeat_task(self.task_store, task_id, broker_id=self.broker_id, state=state)

    def stop_task(self, task_id: str) -> dict[str, Any]:
        return tasks.stop_task(self.task_store, task_id, broker_id=self.broker_id)

    def list_sessions(self) -> dict[str, Any]:
        return sessions.list_sessions(self.store)

    def start_sampler(self, body: dict[str, Any]) -> dict[str, Any]:
        return sampler.start_sampler(self.store, body, task_store=self.task_store, broker_id=self.broker_id)

    def stop_sampler(self) -> dict[str, Any]:
        return sampler.stop_sampler(self.store, task_store=self.task_store)

    def sampler_status(self) -> dict[str, Any]:
        return sampler.sampler_status(self.store, task_store=self.task_store, broker_id=self.broker_id)

    def capture_frame(self, body: dict[str, Any]) -> dict[str, Any]:
        return capture.capture_frame(self.store, body)

    def list_control_plugins(self) -> dict[str, Any]:
        return control.list_control_plugins()

    def diagnose_control(
        self,
        *,
        display: str | None = None,
        backend: str = "auto",
        **selector_kwargs: Any,
    ) -> dict[str, Any]:
        return control.diagnose_control(
            display=display,
            backend=backend,
            **selector_kwargs,
        )

    def list_controls(self, body: dict[str, Any]) -> dict[str, Any]:
        return control.list_controls(body)

    def find_controls(self, body: dict[str, Any]) -> dict[str, Any]:
        return control.find_controls(body)

    def invoke_control(self, body: dict[str, Any]) -> dict[str, Any]:
        return control.invoke_control(body)

    def focus_control(self, body: dict[str, Any]) -> dict[str, Any]:
        return control.focus_control(body)

    def set_control_value(self, body: dict[str, Any]) -> dict[str, Any]:
        return control.set_control_value(body)

    def adopt_window(self, body: dict[str, Any]) -> dict[str, Any]:
        return relay.adopt_window(self.store, body)

    def release_window(self, body: dict[str, Any]) -> dict[str, Any]:
        return relay.release_window(self.store, body)

    def shutdown(self) -> None:
        tasks.shutdown_tasks(self.task_store, self.store, broker_id=self.broker_id)
        sessions.shutdown(self.store)
