from __future__ import annotations

import re
import shutil

from ..capture.linux_xwd import capture_display_png
from ..exceptions import BackendNotAvailableError, CapabilityError, VDisplayError
from ..input.linux_xdotool import LinuxXdotoolInput
from ..models import Capabilities, SessionInfo
from ..discovery import list_outputs, resolve_host_display
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
        self.display = resolve_host_display(display)
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
        _require_xrandr()
        if self._active:
            return

        outputs = _list_connected_outputs(self.display)
        if not outputs:
            raise BackendNotAvailableError("No connected X11 outputs found")

        source = _resolve_output(self.source, outputs, self.display)
        targets = _resolve_mirror_targets(self.target, source, outputs, self.display)

        failures: list[str] = []
        for target in targets:
            self._previous_target_mode = _output_mode(self.display, target)
            ok, failure = _try_mirror(self.display, source, target)
            if ok:
                self._activate_mirror(source, target)
                return
            failures.append(failure)

        raise _mirror_exhausted_error(source, targets, outputs, failures)

    def _activate_mirror(self, source: str, target: str) -> None:
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
        region = _output_capture_region(self.display, self._resolved_source)
        return capture_display_png(self.display, region=region)


def _require_xrandr() -> None:
    if shutil.which("xrandr") is None:
        raise BackendNotAvailableError("xrandr is not installed")


def _resolve_mirror_targets(
    target: str | None,
    source: str,
    outputs: list[str],
    display: str,
) -> list[str]:
    if target is not None:
        return [_resolve_output(target, outputs, display)]
    candidates = _mirror_target_candidates(display, source, outputs)
    if candidates:
        return candidates
    raise BackendNotAvailableError(
        "Mirror requires at least two connected outputs "
        f"(found: {', '.join(outputs)}). Run: vdisplay monitors"
    )


def _try_mirror(display: str, source: str, target: str) -> tuple[bool, str]:
    result = run_command(
        ["xrandr", "--output", target, "--same-as", source],
        env={"DISPLAY": display},
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return True, ""
    err = (result.stderr or result.stdout or "").strip()
    failure = f"--output {target} --same-as {source}"
    if err:
        failure += f": {err}"
    return False, failure


def _mirror_exhausted_error(
    source: str,
    targets: list[str],
    outputs: list[str],
    failures: list[str],
) -> VDisplayError:
    hint = ", ".join(o for o in outputs if o != source)
    message = (
        "xrandr mirror failed for all targets: "
        + "; ".join(failures)
        + f". Try: VD_TARGET={targets[0] if targets else 'HDMI-1'} ./run.sh"
        + (f" (connected: {hint})" if hint else "")
    )
    return VDisplayError(message)


def _list_connected_outputs(display: str) -> list[str]:
    result = run_command(["xrandr", "--query"], env={"DISPLAY": display}, text=True)
    outputs: list[str] = []
    for line in result.stdout.splitlines():
        match = re.match(r"^(\S+)\s+connected", line)
        if match:
            outputs.append(match.group(1))
    return outputs


def _resolve_output(name: str, outputs: list[str], display: str) -> str:
    normalized = name.strip().lower()
    if normalized in {"primary", "default"}:
        primary = _primary_output_from_xrandr(display)
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

    hint = (
        f"Unknown output '{name}'. Connected: {', '.join(outputs)}. "
        "Run: vdisplay monitors"
    )
    if len(outputs) < 2:
        hint += (
            ". Mirror needs at least two outputs; with one monitor use "
            "vdisplay virtual screenshot instead"
        )
    raise BackendNotAvailableError(hint)


def _primary_output_from_xrandr(display: str) -> str | None:
    result = run_command(["xrandr", "--query"], env={"DISPLAY": display}, text=True, check=False)
    for line in result.stdout.splitlines():
        match = re.match(r"^(\S+)\s+connected\s+primary\b", line)
        if match:
            return match.group(1)
    return None


def _output_capture_region(
    display: str,
    output_name: str | None,
) -> tuple[int, int, int, int] | None:
    if not output_name:
        return None
    for output in list_outputs(display):
        if output.get("name") != output_name:
            continue
        x, y = output.get("x"), output.get("y")
        width, height = output.get("width"), output.get("height")
        if None in (x, y, width, height):
            return None
        return int(x), int(y), int(width), int(height)
    return None


def _mirror_target_candidates(display: str, source: str, outputs: list[str]) -> list[str]:
    candidates = [o for o in outputs if o != source]
    primary = _primary_output_from_xrandr(display)
    non_primary = [c for c in candidates if c != primary]
    return non_primary + [c for c in candidates if c == primary]


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
