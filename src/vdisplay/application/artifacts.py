"""Build explicit ArtifactRef lists from handler payloads."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .commands import ArtifactRef, CommandRequest, CommandVerb


def _file_ref(kind: str, path: str | None, *, label: str | None = None, role: str | None = None) -> ArtifactRef | None:
    if not path or not isinstance(path, str):
        return None
    candidate = Path(path)
    if not candidate.is_file():
        return None
    return ArtifactRef(kind=kind, path=str(candidate), label=label, role=role)


def _append_unique(artifacts: list[ArtifactRef], seen: set[str], ref: ArtifactRef | None) -> None:
    if ref is None or ref.path in seen:
        return
    seen.add(ref.path)
    artifacts.append(ref)


def artifacts_from_screenshot(data: dict[str, Any]) -> list[ArtifactRef]:
    artifacts: list[ArtifactRef] = []
    seen: set[str] = set()
    for key, kind in (("path", "screenshot"), ("saved", "screenshot"), ("output", "screenshot")):
        _append_unique(artifacts, seen, _file_ref(kind, data.get(key), label=key))
    preview = data.get("preview")
    if isinstance(preview, dict):
        _append_unique(
            artifacts,
            seen,
            _file_ref("preview", preview.get("preview_path"), label="preview"),
        )
    files = data.get("files")
    if isinstance(files, list):
        for index, item in enumerate(files, start=1):
            if isinstance(item, str):
                _append_unique(artifacts, seen, _file_ref("screenshot", item, label=f"file-{index}"))
            elif isinstance(item, dict):
                _append_unique(
                    artifacts,
                    seen,
                    _file_ref("screenshot", item.get("path"), label=item.get("name") or f"file-{index}"),
                )
    return artifacts


def artifacts_from_control(data: dict[str, Any]) -> list[ArtifactRef]:
    artifacts: list[ArtifactRef] = []
    seen: set[str] = set()

    preview = data.get("preview")
    if isinstance(preview, dict):
        _append_unique(
            artifacts,
            seen,
            _file_ref("preview", preview.get("preview_path"), label="preview", role="preview"),
        )

    screenshot_diff = data.get("screenshot_diff")
    if isinstance(screenshot_diff, dict):
        for side in ("before", "after", "diff"):
            block = screenshot_diff.get(side)
            path = block.get("path") if isinstance(block, dict) else None
            _append_unique(artifacts, seen, _file_ref(side, path, label=side, role=side))

    verification = data.get("verification")
    if isinstance(verification, dict):
        visual = verification.get("visual")
        if isinstance(visual, dict):
            for side in ("before", "after", "diff"):
                block = visual.get(side)
                path = block.get("path") if isinstance(block, dict) else None
                _append_unique(artifacts, seen, _file_ref(side, path, label=f"verify-{side}", role=side))

    for key, kind in (("map_path", "map"), ("map", "map")):
        _append_unique(artifacts, seen, _file_ref(kind, data.get(key), label="map"))

    explicit = data.get("artifacts")
    if isinstance(explicit, dict):
        for kind, path in explicit.items():
            _append_unique(artifacts, seen, _file_ref(str(kind), path if isinstance(path, str) else None, label=str(kind)))

    return artifacts


def build_artifacts(cmd: CommandRequest, data: dict[str, Any]) -> list[ArtifactRef]:
    if cmd.verb == CommandVerb.SCREENSHOT:
        return artifacts_from_screenshot(data)
    if cmd.verb in {
        CommandVerb.CONTROLS_FIND,
        CommandVerb.CONTROL_CLICK,
        CommandVerb.CONTROL_FOCUS,
        CommandVerb.CONTROL_SET_VALUE,
    }:
        return artifacts_from_control(data)
    return []
