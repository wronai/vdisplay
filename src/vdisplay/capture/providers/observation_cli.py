"""Typed observations from native desktop screenshot commands."""

from __future__ import annotations

import contextlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from ..observation import ScreenObservation
from .observation import MonitorSpec, ProviderAvailability, screen_observation_from_png
from .observation_discovery import monitor_specs_from_discovery


def command_candidates() -> list[tuple[str, list[str], bool]]:
    """Return deterministic native screenshot command candidates."""
    if sys.platform == "darwin":
        return [("screencapture", ["screencapture", "-x", "-t", "png", "{path}"], False)]
    if sys.platform.startswith("linux"):
        return [
            ("grim", ["grim", "-"], True),
            ("gnome-screenshot", ["gnome-screenshot", "-f", "{path}"], False),
            ("spectacle", ["spectacle", "-b", "-n", "-o", "{path}"], False),
            ("maim", ["maim", "{path}"], False),
            ("scrot", ["scrot", "--overwrite", "{path}"], False),
        ]
    return []


def run_png_command(binary: str, template: list[str], stdout_png: bool) -> bytes:
    """Execute one resolved screenshot command without invoking a shell."""
    executable = shutil.which(binary)
    if not executable:
        raise RuntimeError(f"{binary} not found")
    if stdout_png:
        command = [executable if part == binary else part for part in template]
        result = subprocess.run(command, capture_output=True, timeout=15, check=False)
        if result.returncode == 0 and result.stdout:
            return result.stdout
        stderr = (result.stderr or b"").decode("utf-8", "replace").strip()
        raise RuntimeError(f"{binary} failed ({result.returncode}): {stderr[-300:]}")

    temporary_path = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temporary:
            temporary_path = temporary.name
        with contextlib.suppress(OSError):
            os.unlink(temporary_path)
        command = [
            executable if part == binary else part.format(path=temporary_path)
            for part in template
        ]
        result = subprocess.run(command, capture_output=True, timeout=15, check=False)
        if result.returncode != 0:
            stderr = (result.stderr or b"").decode("utf-8", "replace").strip()
            raise RuntimeError(f"{binary} failed ({result.returncode}): {stderr[-300:]}")
        if not os.path.isfile(temporary_path):
            raise RuntimeError(f"{binary} did not write {temporary_path}")
        return Path(temporary_path).read_bytes()
    finally:
        if temporary_path:
            with contextlib.suppress(OSError):
                os.unlink(temporary_path)


class CliToolsObservationProvider:
    name = "cli_tools"
    streams = False

    def availability(self) -> ProviderAvailability:
        for binary, _, _ in command_candidates():
            if shutil.which(binary):
                return ProviderAvailability(available=True, reason=f"{binary} found")
        return ProviderAvailability(
            available=False,
            reason="no supported CLI screenshot tool",
            install_hint="install grim (wlroots) or scrot (X11)",
        )

    def list_monitors(self) -> list[MonitorSpec]:
        return monitor_specs_from_discovery()

    def capture_one(self, monitor_id: int | None, scale: float) -> ScreenObservation:
        del monitor_id, scale  # Native command providers preserve full-size payloads.
        errors: list[str] = []
        for binary, template, stdout_png in command_candidates():
            try:
                payload = run_png_command(binary, template, stdout_png)
                return screen_observation_from_png(
                    payload,
                    monitor_id=-1,
                    scale=1.0,
                    output=binary,
                    provider=self.name,
                )
            except Exception as exc:  # noqa: BLE001 - optional desktop tools vary.
                errors.append(f"{binary}: {exc}")
        detail = "; ".join(errors)
        raise RuntimeError(
            f"no native screenshot command worked{'; ' + detail if detail else ''}"
        )

    def capture_all(self, scale: float) -> list[ScreenObservation]:
        return [self.capture_one(None, scale)]


class GrimObservationProvider:
    name = "grim"
    streams = False

    def availability(self) -> ProviderAvailability:
        if not shutil.which("grim"):
            return ProviderAvailability(
                available=False,
                reason="grim not installed",
                install_hint="apt install grim",
            )
        return ProviderAvailability(available=True, reason="grim (wlroots screencopy)")

    def list_monitors(self) -> list[MonitorSpec]:
        return monitor_specs_from_discovery()

    def capture_one(self, monitor_id: int | None, scale: float) -> ScreenObservation:
        del monitor_id
        payload = run_png_command("grim", ["grim", "-"], True)
        return screen_observation_from_png(
            payload,
            monitor_id=0,
            scale=scale,
            output="grim",
            provider=self.name,
        )

    def capture_all(self, scale: float) -> list[ScreenObservation]:
        return [self.capture_one(None, scale)]


__all__ = [
    "CliToolsObservationProvider",
    "GrimObservationProvider",
    "command_candidates",
    "run_png_command",
]
