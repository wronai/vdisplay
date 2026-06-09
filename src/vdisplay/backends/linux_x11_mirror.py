from __future__ import annotations

import os
import re
import shutil

from ..capture.linux_xwd import capture_display_png
from ..exceptions import BackendNotAvailableError, CapabilityError
from ..input.linux_xdotool import LinuxXdotoolInput
from ..models import Capabilities, SessionInfo
from ..utils import run_command
from .base import BaseBackend


class LinuxX11MirrorBackend(BaseBackend):
    name = "linux-x11-mirror"

    def __init__(
        self,
        source: str = "primary",
        target: str | None = None,
        display: str | None = None,
    ) -> None:
        super().__init__()
        self.source = source
        self.target = target
        self.display = display or os.environ.get("DISPLAY", ":0")
        self._previous_target_mode: str | None = None
        self._resolved_source: str | None = None
        self._resolved_target: str | None = None
        self.pointer = LinuxXdotoolInput(self.display)

    def capabilities(self) -> Capabilities:
        return Capabilities(
            capture=True,
            input_control=True,
            mirror_config=True,
            isolation=False,
        )

    def info(self) -> SessionInfo:
        return SessionInfo(
            kind="mirror",
            backend=self.name,
            active=self._active,
            source=self._resolved_source or self.source,
            target=self._resolved_target or self.target,
            metadata={"display": self.display},
        )

    def start(self) -> None:
        if shutil.which("xrandr") is None:
            raise BackendNotAvailableError("xrandr is not installed")
        if self._active:
            return

        outputs = _list_connected_outputs(self.display)
        if not outputs:
            raise BackendNotAvailableError("No connected X11 outputs found")

        source = _resolve_output(self.source, outputs)
        target = self.target
        if target is None:
            candidates = [o for o in outputs if o != source]
            if not candidates:
                raise BackendNotAvailableError(
                    "Mirror requires at least two connected outputs; specify --target explicitly"
                )
            target = candidates[0]
        else:
            target = _resolve_output(target, outputs)

        self._previous_target_mode = _output_mode(self.display, target)
        run_command(
            ["xrandr", "--output", target, "--same-as", source],
            env={"DISPLAY": self.display},
            text=True,
        )

        self._resolved_source = source
        self._resolved_target = target
        self._active = True

    def stop(self) -> None:
        if not self._active or self._resolved_target is None:
            self._active = False
            return

        if self._previous_target_mode == "off":
            run_command(
                ["xrandr", "--output", self._resolved_target, "--off"],
                env={"DISPLAY": self.display},
                text=True,
                check=False,
            )
        elif self._previous_target_mode:
            run_command(
                ["xrandr", "--output", self._resolved_target, "--mode", self._previous_target_mode],
                env={"DISPLAY": self.display},
                text=True,
                check=False,
            )
        else:
            run_command(
                ["xrandr", "--output", self._resolved_target, "--auto"],
                env={"DISPLAY": self.display},
                text=True,
                check=False,
            )

        self._active = False

    def screenshot_bytes(self) -> bytes:
        if not self._active:
            raise CapabilityError("Mirror session is not active")
        return capture_display_png(self.display)


def _list_connected_outputs(display: str) -> list[str]:
    result = run_command(["xrandr", "--query"], env={"DISPLAY": display}, text=True)
    outputs: list[str] = []
    for line in result.stdout.splitlines():
        match = re.match(r"^(\S+)\s+connected", line)
        if match:
            outputs.append(match.group(1))
    return outputs


def _resolve_output(name: str, outputs: list[str]) -> str:
    normalized = name.strip().lower()
    if normalized in {"primary", "default"}:
        primary = _primary_output(outputs)
        if primary:
            return primary
        if outputs:
            return outputs[0]
        raise BackendNotAvailableError("No outputs available to resolve primary display")

    if normalized.startswith("virtual:"):
        index = int(normalized.split(":", 1)[1]) - 1
        if index < 0 or index >= len(outputs):
            raise BackendNotAvailableError(f"Virtual output index out of range: {name}")
        return outputs[index]

    for output in outputs:
        if output.lower() == normalized:
            return output
    raise BackendNotAvailableError(f"Unknown output '{name}'. Connected: {', '.join(outputs)}")


def _primary_output(outputs: list[str]) -> str | None:
    for output in outputs:
        if output.lower() in {"edp", "edp-1", "lvds1", "lvds-1", "hdmi-1", "dp-1"}:
            return output
    return outputs[0] if outputs else None


def _output_mode(display: str, output: str) -> str | None:
    result = run_command(["xrandr", "--query"], env={"DISPLAY": display}, text=True)
    in_block = False
    for line in result.stdout.splitlines():
        if line.startswith(output + " "):
            if " disconnected" in line:
                return "off"
            in_block = True
            continue
        if in_block:
            if line.startswith(" "):
                if "*" in line:
                    return line.strip().split()[0]
            else:
                break
    return None
