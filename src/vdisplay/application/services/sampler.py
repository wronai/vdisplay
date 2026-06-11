"""Continuous frame sampling (CLI blocking or agent background worker)."""

from __future__ import annotations

import signal
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from ...capture.policy import CaptureMode
from .sampler_loop import FrameFormat, SamplerLoop, SamplerLoopConfig, validate_sampler_config


@dataclass
class SamplerConfig:
    interval_s: float = 5.0
    mode: CaptureMode = "desktop"
    source: str | None = None
    display: str | None = None
    vd_display: str = ":99"
    output_dir: str = "./captures"
    max_frames: int | None = None
    dedupe: bool = True
    skip_img2nl: bool = True
    width: int = 1280
    height: int = 720
    format: FrameFormat = "png"

    def to_loop_config(self) -> SamplerLoopConfig:
        return SamplerLoopConfig(
            interval_s=self.interval_s,
            mode=self.mode,
            source=self.source,
            display=self.display,
            vd_display=self.vd_display,
            output_dir=self.output_dir,
            max_frames=self.max_frames,
            dedupe=self.dedupe,
            width=self.width,
            height=self.height,
            format=self.format,
        )


def run_sampler(
    config: SamplerConfig,
    *,
    on_frame: Any | None = None,
) -> dict[str, Any]:
    """Blocking sampler loop until max_frames or SIGINT."""
    from . import capture as capture_svc

    loop_config = config.to_loop_config()
    validate_sampler_config(loop_config)

    def capture_fn(**kwargs: Any) -> dict[str, Any]:
        return capture_svc.capture_screenshot(
            output=kwargs["output"],
            display=kwargs.get("display"),
            source=kwargs.get("source"),
            mode=kwargs.get("mode", "host"),
            vd_display=kwargs.get("vd_display", ":99"),
            width=kwargs.get("width", 1280),
            height=kwargs.get("height", 720),
            skip_img2nl=config.skip_img2nl,
        )

    loop = SamplerLoop(loop_config, capture_fn)
    stop = False

    def _handle_sigint(_signum: int, _frame: Any) -> None:
        nonlocal stop
        stop = True
        loop._stop.set()

    previous = signal.signal(signal.SIGINT, _handle_sigint)
    loop.start()
    try:
        while loop.state.running and not stop:
            before = loop.state.frames_saved
            time.sleep(0.1)
            if on_frame is not None and loop.state.frames_saved > before:
                on_frame(loop.state.recent_frames[-1])
    finally:
        signal.signal(signal.SIGINT, previous)
        result = loop.stop()

    return {
        **result,
        "frames": list(loop.state.recent_frames),
        "stopped": True,
    }


def start_sampler_via_agent(client, config: SamplerConfig) -> dict[str, Any]:
    return client.sampler_start(
        interval_s=config.interval_s,
        mode=config.mode,
        source=config.source,
        display=config.display,
        vd_display=config.vd_display,
        out_dir=config.output_dir,
        max_frames=config.max_frames,
        dedupe=config.dedupe,
        width=config.width,
        height=config.height,
        format=config.format,
    )
