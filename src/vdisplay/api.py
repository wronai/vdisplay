from __future__ import annotations

import platform
import sys
from dataclasses import asdict

from .backends.linux_x11_mirror import LinuxX11MirrorBackend
from .backends.linux_x11_relay import LinuxX11RelayBackend
from .backends.linux_xvfb import LinuxXvfbBackend
from .exceptions import BackendNotAvailableError


def _default_virtual_backend() -> str:
    if sys.platform.startswith("linux"):
        return "xvfb"
    return "xvfb"


def _default_mirror_backend() -> str:
    if sys.platform.startswith("linux"):
        return "x11"
    return "stub"


def _default_relay_backend() -> str:
    if sys.platform.startswith("linux"):
        return "x11"
    return "x11"


class VirtualDisplaySession:
    def __init__(self, backend) -> None:
        self.backend = backend

    @classmethod
    def create(
        cls,
        width: int = 1920,
        height: int = 1080,
        backend: str | None = None,
        display: str = ":99",
    ):
        backend = backend or _default_virtual_backend()
        if backend == "xvfb":
            if not sys.platform.startswith("linux"):
                raise BackendNotAvailableError("xvfb backend is only available on Linux")
            return cls(LinuxXvfbBackend(width=width, height=height, display=display))
        raise BackendNotAvailableError(f"Unknown virtual backend: {backend}")

    def start(self) -> None:
        self.backend.start()

    def stop(self) -> None:
        self.backend.stop()

    def launch(self, command):
        return self.backend.launch(command)

    def screenshot_bytes(self) -> bytes:
        return self.backend.screenshot_bytes()

    def save_screenshot(self, path: str) -> str:
        return self.backend.save_screenshot(path)

    def adopt_window(self, *, match_title: str | None = None, window_id: str | None = None) -> str:
        return self.backend.adopt_window(match_title=match_title, window_id=window_id)

    def release_window(self, *, match_title: str | None = None, window_id: str | None = None) -> str:
        return self.backend.release_window(match_title=match_title, window_id=window_id)

    def info(self) -> dict:
        return asdict(self.backend.info())

    def capabilities(self) -> dict:
        return asdict(self.backend.capabilities())


class MirrorSession:
    def __init__(self, backend) -> None:
        self.backend = backend
        self.pointer = getattr(backend, "pointer", None)

    @classmethod
    def create(
        cls,
        source: str = "primary",
        target: str | None = None,
        backend: str | None = None,
        display: str | None = None,
    ):
        backend = backend or _default_mirror_backend()
        if backend in {"x11", "linux-x11", "linux-x11-mirror"}:
            if not sys.platform.startswith("linux"):
                raise BackendNotAvailableError("linux-x11 mirror backend is only available on Linux")
            return cls(LinuxX11MirrorBackend(source=source, target=target, display=display))
        if backend == "stub":
            from .backends.mirror_stub import MirrorStubBackend

            return cls(MirrorStubBackend(source=source, target=target or "virtual:1"))
        raise BackendNotAvailableError(f"Unknown mirror backend: {backend}")

    def start(self) -> None:
        self.backend.start()

    def stop(self) -> None:
        self.backend.stop()

    def screenshot_bytes(self) -> bytes:
        return self.backend.screenshot_bytes()

    def save_screenshot(self, path: str) -> str:
        return self.backend.save_screenshot(path)

    def info(self) -> dict:
        return asdict(self.backend.info())

    def capabilities(self) -> dict:
        return asdict(self.backend.capabilities())


class WindowRelaySession:
    def __init__(self, backend) -> None:
        self.backend = backend

    @classmethod
    def create(cls, backend: str | None = None, display: str | None = None):
        backend = backend or _default_relay_backend()
        if backend in {"x11", "linux-x11", "linux-x11-relay"}:
            if not sys.platform.startswith("linux"):
                raise BackendNotAvailableError("linux-x11 relay backend is only available on Linux")
            return cls(LinuxX11RelayBackend(display=display))
        raise BackendNotAvailableError(f"Unknown relay backend: {backend}")

    def start(self) -> None:
        self.backend.start()

    def stop(self) -> None:
        self.backend.stop()

    def adopt_window(
        self,
        *,
        match_title: str | None = None,
        window_id: str | None = None,
        match_class: str | None = None,
        match_pid: int | None = None,
        match_app: str | None = None,
        target: str = "offscreen",
    ) -> str:
        return self.backend.adopt_window(
            match_title=match_title,
            window_id=window_id,
            match_class=match_class,
            match_pid=match_pid,
            match_app=match_app,
            target=target,
        )

    def release_window(
        self,
        *,
        match_title: str | None = None,
        window_id: str | None = None,
    ) -> str:
        return self.backend.release_window(match_title=match_title, window_id=window_id)

    def list_adopted(self) -> list[dict]:
        return self.backend.list_adopted()

    def info(self) -> dict:
        return asdict(self.backend.info())

    def capabilities(self) -> dict:
        return asdict(self.backend.capabilities())


def platform_summary() -> dict:
    return {
        "platform": platform.system(),
        "python": platform.python_version(),
        "virtual_backend": _default_virtual_backend(),
        "mirror_backend": _default_mirror_backend(),
        "relay_backend": _default_relay_backend(),
    }
