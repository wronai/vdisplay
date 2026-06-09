#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

from screenshot_meta import meta_path_for, png_dimensions


def validate_image_and_meta(image_path: Path) -> list[str]:
    errors: list[str] = []
    meta_path = meta_path_for(image_path)

    if not image_path.exists():
        return [f"missing image: {image_path}"]
    if not meta_path.exists():
        return [f"missing meta sidecar: {meta_path}"]

    try:
        width, height = png_dimensions(image_path)
    except ValueError as exc:
        return [f"invalid png {image_path}: {exc}"]

    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"invalid meta json {meta_path}: {exc}"]

    for key in ("nl", "width", "height", "bytes", "path", "format"):
        if key not in meta:
            errors.append(f"{meta_path}: missing key {key!r}")

    if meta.get("format") != "PNG":
        errors.append(f"{meta_path}: format must be PNG")

    if meta.get("width") != width or meta.get("height") != height:
        errors.append(
            f"{meta_path}: meta size {meta.get('width')}x{meta.get('height')} "
            f"!= png size {width}x{height}"
        )

    actual_bytes = image_path.stat().st_size
    if meta.get("bytes") != actual_bytes:
        errors.append(f"{meta_path}: bytes {meta.get('bytes')} != file size {actual_bytes}")

    if not str(meta.get("nl", "")).strip():
        errors.append(f"{meta_path}: empty nl description")

    return errors


def validate_directory(root: Path) -> list[str]:
    errors: list[str] = []
    images = sorted(root.glob("*.png"))
    if not images:
        return [f"no png artifacts in {root}"]

    for image_path in images:
        errors.extend(validate_image_and_meta(image_path))
    return errors


def main(argv: list[str] | None = None) -> int:
    args = list(argv or sys.argv[1:])
    if not args:
        print("usage: validate_artifacts.py <output-dir> [more-dirs...]", file=sys.stderr)
        return 2

    errors: list[str] = []
    for raw in args:
        errors.extend(validate_directory(Path(raw)))

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    print(f"ok: validated artifacts in {', '.join(args)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
