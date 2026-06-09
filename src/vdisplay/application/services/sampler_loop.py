"""Background-capable sampler loop (CLI blocking or agent worker thread)."""

from __future__ import annotations

import hashlib
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from ...capture.policy import assess_unattended_capture
from ...exceptions import VDisplayError

FrameFormat = Literal["png", "webp", "jpeg"]
CaptureFn = Callable[..., dict[str, Any]]
RecoverFn = Callable[[], bool]


@dataclass
class SamplerLoopConfig:
    interval_s: float = 1.0
    mode: str = "desktop"
    source: str | None = None
    display: str | None = None
    vd_display: str = ":99"
    output_dir: str = "./captures"
    max_frames: int | None = None
    dedupe: bool = True
    width: int = 1280
    height: int = 720
    format: FrameFormat = "png"


@dataclass
class SamplerLoopState:
    running: bool = False
    frames_saved: int = 0
    frames_skipped_dedupe: int = 0
    last_frame_at: float | None = None
    last_error: str | None = None
    requires_reconsent: bool = False
    recovery_attempts: int = 0
    capture_mode: str = ""
    out_dir: str = ""
    recent_frames: list[dict[str, Any]] = field(default_factory=list)


def resolve_capture_mode(mode: str, *, display: str | None) -> str:
    if mode == "strict":
        return "virtual"
    if mode == "desktop":
        return "host"
    if mode == "unattended":
        contract = assess_unattended_capture(display=display)
        return "virtual" if contract.recommended_profile == "virtual" else "host"
    return "host"


def is_screencast_recoverable_error(error: str) -> bool:
    lowered = error.lower()
    return any(
        token in lowered
        for token in (
            "blank frame",
            "stale screencast",
            "no active session",
            "screencast capture blank",
        )
    )


def frame_extension(fmt: FrameFormat) -> str:
    return {"png": "png", "webp": "webp", "jpeg": "jpg"}[fmt]


def transcode_frame(path: Path, fmt: FrameFormat) -> Path:
    if fmt == "png":
        return path
    try:
        from PIL import Image
    except ImportError:
        from ...utils import auto_install_package
        auto_install_package("vdisplay[pillow]")
        from PIL import Image

    target = path.with_suffix(f".{frame_extension(fmt)}")
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        if fmt == "webp":
            rgb.save(target, format="WEBP", quality=85)
        else:
            rgb.save(target, format="JPEG", quality=85)
    if target != path:
        path.unlink(missing_ok=True)
    return target


def validate_sampler_config(
    config: SamplerLoopConfig,
    *,
    screencast_ready: bool | None = None,
) -> dict[str, Any]:
    capture_mode = resolve_capture_mode(config.mode, display=config.display)
    contract = assess_unattended_capture(
        display=config.vd_display if capture_mode == "virtual" else config.display,
        screencast_ready=screencast_ready,
    )
    if config.mode == "unattended" and not contract.supports_unattended_capture:
        raise VDisplayError(
            "unattended mode not available — "
            f"{', '.join(contract.reasons)}. "
            "Try: vdisplay sampler start --mode strict --vd-display :99"
        )
    if capture_mode == "host" and contract.requires_user_consent and not contract.supports_unattended_capture:
        raise VDisplayError(
            "host sampling needs active ScreenCast — "
            "run: vdisplay agent screencast start"
        )
    return {"capture_mode": capture_mode, "contract": contract.to_dict()}


class SamplerLoop:
    """Capture frames on an interval; safe to run in a daemon thread."""

    def __init__(
        self,
        config: SamplerLoopConfig,
        capture_fn: CaptureFn,
        *,
        screencast_ready: bool | None = None,
        recover_fn: RecoverFn | None = None,
    ) -> None:
        self.config = config
        self._capture_fn = capture_fn
        self._screencast_ready = screencast_ready
        self._recover_fn = recover_fn
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self.state = SamplerLoopState()
        self._meta: dict[str, Any] = {}

    def start(self) -> dict[str, Any]:
        with self._lock:
            if self.state.running:
                raise VDisplayError("sampler already running")
            bootstrap = validate_sampler_config(
                self.config,
                screencast_ready=self._screencast_ready,
            )
            self._meta = bootstrap
            self.state.capture_mode = bootstrap["capture_mode"]
            self.state.out_dir = str(Path(self.config.output_dir).expanduser().resolve())
            self._stop.clear()
            self._thread = threading.Thread(target=self._run, name="vdisplay-sampler", daemon=True)
            self.state.running = True
            self._thread.start()
        return self.status()

    def stop(self) -> dict[str, Any]:
        self._stop.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=max(5.0, self.config.interval_s * 2))
        with self._lock:
            self.state.running = False
        return self.status()

    def status(self) -> dict[str, Any]:
        with self._lock:
            return {
                "ok": True,
                "running": self.state.running,
                "mode": self.config.mode,
                "capture_mode": self.state.capture_mode,
                "interval_s": self.config.interval_s,
                "format": self.config.format,
                "out_dir": self.state.out_dir,
                "frames_saved": self.state.frames_saved,
                "frames_skipped_dedupe": self.state.frames_skipped_dedupe,
                "last_frame_at": self.state.last_frame_at,
                "last_error": self.state.last_error,
                "requires_reconsent": self.state.requires_reconsent,
                "recovery_attempts": self.state.recovery_attempts,
                "contract": self._meta.get("contract"),
                "recent_frames": list(self.state.recent_frames[-5:]),
            }

    def _run(self) -> None:
        out_dir = Path(self.config.output_dir).expanduser()
        out_dir.mkdir(parents=True, exist_ok=True)
        last_hash: str | None = None
        index = 0
        consecutive_errors = 0

        while not self._stop.is_set():
            if self.config.max_frames is not None and index >= self.config.max_frames:
                break
            try:
                last_hash, index = self._capture_frame_iteration(out_dir, index, last_hash)
                consecutive_errors = 0
            except Exception as exc:
                if self._handle_capture_error(str(exc)):
                    consecutive_errors = 0
                    continue
                consecutive_errors += 1
                if consecutive_errors >= 3:
                    break

            if self.config.max_frames is not None and index >= self.config.max_frames:
                break
            if self._stop.wait(timeout=max(0.05, self.config.interval_s)):
                break

        with self._lock:
            self.state.running = False

    def _capture_frame_iteration(self, out_dir: Path, index: int, last_hash: str | None) -> tuple[str | None, int]:
        png_path = out_dir / f"frame-{index:06d}.png"
        meta = self._capture_fn(
            output=str(png_path),
            display=self.config.display,
            source=self.config.source,
            mode=self.state.capture_mode,
            vd_display=self.config.vd_display,
            width=self.config.width,
            height=self.config.height,
        )
        saved = transcode_frame(png_path, self.config.format)
        if saved != png_path:
            meta["path"] = str(saved.resolve())
            meta["bytes"] = saved.stat().st_size

        frame_hash = hashlib.sha256(saved.read_bytes()).hexdigest()[:16]
        meta["frame_index"] = index
        meta["captured_at"] = time.time()
        meta["frame_hash"] = frame_hash
        meta["format"] = self.config.format

        if self.config.dedupe and frame_hash == last_hash:
            saved.unlink(missing_ok=True)
            with self._lock:
                self.state.frames_skipped_dedupe += 1
            return last_hash, index

        with self._lock:
            self.state.frames_saved += 1
            self.state.last_frame_at = meta["captured_at"]
            self.state.last_error = None
            self.state.recent_frames.append(
                {
                    "frame_index": index,
                    "path": meta.get("path"),
                    "bytes": meta.get("bytes"),
                    "method": meta.get("method"),
                    "format": self.config.format,
                }
            )
            if len(self.state.recent_frames) > 20:
                self.state.recent_frames = self.state.recent_frames[-20:]
        return frame_hash, index + 1

    def _handle_capture_error(self, err: str) -> bool:
        with self._lock:
            self.state.last_error = err

        if self._recover_fn is not None and is_screencast_recoverable_error(err):
            with self._lock:
                self.state.recovery_attempts += 1
            recovered = self._recover_fn()
            with self._lock:
                if recovered:
                    self.state.last_error = None
                    self.state.requires_reconsent = False
                else:
                    self.state.requires_reconsent = True
            return recovered
        return False
