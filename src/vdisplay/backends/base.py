from __future__ import annotations

from dataclasses import asdict
from typing import Sequence

from ..exceptions import CapabilityError
from ..models import Capabilities, SessionInfo


class BaseBackend:
    name = "base"

    def __init__(self) -> None:
        self._active = False

    def capabilities(self) -> Capabilities:
        return Capabilities()

    def info(self) -> SessionInfo:
        return SessionInfo(kind="unknown", backend=self.name, active=self._active)

    def start(self) -> None:
        self._active = True

    def stop(self) -> None:
        self._active = False

    def launch(self, command: Sequence[str]) -> int | None:
        raise CapabilityError(f"Backend {self.name} does not support launch()")

    def screenshot_bytes(self) -> bytes:
        raise CapabilityError(f"Backend {self.name} does not support screenshot capture")

    def save_screenshot(self, path: str) -> str:
        data = self.screenshot_bytes()
        with open(path, "wb") as f:
            f.write(data)
        return path

    def adopt_window(
        self,
        *,
        match_title: str | None = None,
        window_id: str | None = None,
        target: str = "offscreen",
    ) -> str:
        raise CapabilityError(f"Backend {self.name} does not support adopt_window()")

    def release_window(
        self,
        *,
        match_title: str | None = None,
        window_id: str | None = None,
    ) -> str:
        raise CapabilityError(f"Backend {self.name} does not support release_window()")

    def as_dict(self) -> dict:
        return asdict(self.info())
