"""Continuous frame sampling (watch loop)."""

from __future__ import annotations

import hashlib
import signal
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from ...capture.policy import CaptureMode, assess_unattended_capture
from ...exceptions import VDisplayError


@dataclass
class SamplerConfig:
    interval_s: float = 1.0
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


def _resolve_capture_mode(config: SamplerConfig) -> str:
    if config.mode == "strict":
        return "virtual"
    if config.mode == "desktop":
        return "host"
    if config.mode == "unattended":
        contract = assess_unattended_capture(display=config.display)
        return "virtual" if contract.recommended_profile == "virtual" else "host"
    return "host"


def run_sampler(
    config: SamplerConfig,
    *,
    on_frame: Any | None = None,
) -> dict[str, Any]:
    """
    Capture frames in a loop until max_frames, SIGINT, or error.

    on_frame(meta) is called after each saved frame (for CLI progress).
    """
    from . import capture as capture_svc

    out_dir = Path(config.output_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    contract = assess_unattended_capture(display=config.display)
    if config.mode in {"strict", "unattended"} and not contract.supports_unattended_capture:
        if config.mode == "strict":
            raise VDisplayError(
                "strict mode requires owned virtual display (:99); "
                f"got {contract.session_type}: {', '.join(contract.reasons)}"
            )

    capture_mode = _resolve_capture_mode(config)
    if capture_mode == "host" and contract.requires_user_consent and not contract.supports_unattended_capture:
        raise VDisplayError(
            "host sampling needs active ScreenCast on Wayland — "
            "run: vdisplay agent serve && vdisplay agent screencast start. "
            f"Or use: vdisplay sampler start --mode strict --vd-display :99"
        )

    stop = False

    def _handle_sigint(_signum: int, _frame: Any) -> None:
        nonlocal stop
        stop = True

    previous = signal.signal(signal.SIGINT, _handle_sigint)
    frames: list[dict[str, Any]] = []
    last_hash: str | None = None
    skipped = 0
    index = 0

    try:
        while not stop:
            if config.max_frames is not None and index >= config.max_frames:
                break

            name = f"frame-{index:06d}.png"
            output = str(out_dir / name)
            meta = capture_svc.capture_screenshot(
                output=output,
                display=config.display,
                source=config.source,
                mode=capture_mode,
                vd_display=config.vd_display,
                width=config.width,
                height=config.height,
                skip_img2nl=config.skip_img2nl,
            )
            meta["frame_index"] = index
            meta["captured_at"] = time.time()

            frame_hash = hashlib.sha256(Path(output).read_bytes()).hexdigest()[:16]
            meta["frame_hash"] = frame_hash

            if config.dedupe and frame_hash == last_hash:
                Path(output).unlink(missing_ok=True)
                skipped += 1
            else:
                last_hash = frame_hash
                frames.append(meta)
                if on_frame is not None:
                    on_frame(meta)
                index += 1

            if config.max_frames is not None and index >= config.max_frames:
                break
            if stop:
                break
            time.sleep(max(0.05, config.interval_s))
    finally:
        signal.signal(signal.SIGINT, previous)

    return {
        "ok": True,
        "mode": config.mode,
        "capture_mode": capture_mode,
        "out_dir": str(out_dir.resolve()),
        "frames_saved": len(frames),
        "frames_skipped_dedupe": skipped,
        "contract": contract.to_dict(),
        "frames": frames,
        "stopped": stop,
    }
