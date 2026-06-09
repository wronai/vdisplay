from __future__ import annotations

import json
import struct
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def examples_common_dir() -> Path:
    here = Path(__file__).resolve().parent
    if (here / "screenshot_meta.py").exists():
        return here
    raise RuntimeError("examples/common directory not found")


def ensure_common_on_path() -> None:
    common = examples_common_dir()
    if str(common) not in sys.path:
        sys.path.insert(0, str(common))


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def meta_path_for(image_path: str | Path) -> Path:
    path = Path(image_path)
    return path.with_suffix(path.suffix + ".meta.json")


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        signature = handle.read(8)
        if signature != b"\x89PNG\r\n\x1a\n":
            raise ValueError(f"not a PNG file: {path}")

        while True:
            length_bytes = handle.read(4)
            if len(length_bytes) != 4:
                break
            length = struct.unpack(">I", length_bytes)[0]
            chunk_type = handle.read(4)
            if chunk_type == b"IHDR":
                width, height = struct.unpack(">II", handle.read(8))
                return width, height
            handle.seek(length + 4, 1)


def describe_screenshot_nl(
    *,
    width: int,
    height: int,
    label: str | None = None,
    session_kind: str | None = None,
    display: str | None = None,
    phase: str | None = None,
    monitors: list[dict[str, Any]] | None = None,
    windows: list[dict[str, Any]] | None = None,
) -> str:
    if label:
        headline = label
    elif session_kind:
        headline = f"Screenshot of {session_kind} display {display or 'unknown'}"
    else:
        headline = "Screenshot"

    if phase:
        headline = f"{headline} ({phase.replace('_', ' ')})"

    parts = [headline, f"({width}×{height} PNG)"]

    if monitors:
        names = [str(m.get("name")) for m in monitors if m.get("name")]
        if names:
            parts.append(f"monitors: {', '.join(names)}")

    if windows:
        apps = [
            str(w.get("app_label"))
            for w in windows
            if w.get("app_label") and not w.get("is_internal")
        ]
        if apps:
            unique = sorted(set(apps))
            parts.append(f"visible apps: {', '.join(unique[:8])}")

    return " ".join(parts) + "."


def build_screenshot_meta(
    image_path: str | Path,
    *,
    label: str | None = None,
    session_kind: str | None = None,
    display: str | None = None,
    phase: str | None = None,
    session_info: dict[str, Any] | None = None,
    monitors: list[dict[str, Any]] | None = None,
    windows: list[dict[str, Any]] | None = None,
    state: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    path = Path(image_path)
    width, height = png_dimensions(path)
    payload: dict[str, Any] = {
        "path": str(path),
        "meta_path": str(meta_path_for(path)),
        "format": "PNG",
        "width": width,
        "height": height,
        "bytes": path.stat().st_size,
        "captured_at": datetime.now(UTC).isoformat(),
        "session_kind": session_kind,
        "display": display,
        "phase": phase,
        "nl": describe_screenshot_nl(
            width=width,
            height=height,
            label=label,
            session_kind=session_kind,
            display=display,
            phase=phase,
            monitors=monitors,
            windows=windows,
        ),
    }
    if session_info is not None:
        payload["session"] = session_info
    if monitors is not None:
        payload["monitors"] = monitors
    if windows is not None:
        payload["windows"] = windows
    if state is not None:
        payload["state"] = state
    if extra:
        payload.update(extra)
    return payload


def write_screenshot_meta(image_path: str | Path, **kwargs: Any) -> dict[str, Any]:
    meta = build_screenshot_meta(image_path, **kwargs)
    meta_file = meta_path_for(image_path)
    meta_file.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def save_png_with_meta(
    image_path: str | Path,
    png_bytes: bytes,
    **kwargs: Any,
) -> dict[str, Any]:
    if not png_bytes.startswith(PNG_SIGNATURE):
        raise ValueError("capture did not produce a valid PNG image")
    path = Path(image_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png_bytes)
    return write_screenshot_meta(path, **kwargs)


def print_artifact(meta: dict[str, Any]) -> None:
    print(json.dumps({"artifact": meta}, indent=2))
