"""KMS/DRM scanout capture via ffmpeg kmsgrab (GPU driver framebuffer, no portal)."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from ...exceptions import VDisplayError
from ...utils import require_command


def _drm_devices() -> list[Path]:
    dri = Path("/dev/dri")
    if not dri.is_dir():
        return []
    devices: list[Path] = []
    for path in sorted(dri.glob("card*")):
        if path.is_char_device() and not path.name.endswith("card"):
            devices.append(path)
    return devices


class DrmProvider:
    name = "drm"

    def available(self) -> tuple[bool, str]:
        if not shutil.which("ffmpeg"):
            return False, "ffmpeg not installed"
        if not _drm_devices():
            return False, "no /dev/dri/card* device"
        return True, "KMS scanout via ffmpeg kmsgrab"

    def capture_full(self) -> bytes:
        return self._capture(None)

    def capture_region(self, region: tuple[int, int, int, int]) -> bytes:
        return self._capture(region)

    def _capture(self, region: tuple[int, int, int, int] | None) -> bytes:
        require_command("ffmpeg")
        devices = _drm_devices()
        if not devices:
            raise VDisplayError("no DRM device available")

        errors: list[str] = []
        for device in devices:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                out = Path(tmp.name)
            try:
                args = [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-f",
                    "kmsgrab",
                    "-device",
                    str(device),
                    "-i",
                    "-",
                ]
                if region is not None:
                    x, y, width, height = region
                    args.extend(["-vf", f"crop={width}:{height}:{x}:{y}"])
                args.extend(["-frames:v", "1", "-y", str(out)])
                result = subprocess.run(
                    args,
                    capture_output=True,
                    text=True,
                    timeout=20,
                    check=False,
                )
                if result.returncode != 0 or not out.is_file() or out.stat().st_size < 64:
                    err = (result.stderr or result.stdout or "kmsgrab failed").strip()
                    errors.append(f"{device.name}: {err}")
                    continue
                return out.read_bytes()
            except subprocess.TimeoutExpired:
                errors.append(f"{device.name}: timeout")
            finally:
                out.unlink(missing_ok=True)

        raise VDisplayError(
            "DRM/KMS capture failed. "
            "Ensure user is in the `video` group for driver-level scanout access. "
            f"Tried: {'; '.join(errors) or 'no devices'}"
        )
