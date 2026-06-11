"""Persist automation metadata under project .vdisplay/."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..config_options import ConfigOptions, get_runtime_options
from ..project_config import ProjectConfig, ensure_metadata_layout


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def start_auto_run(project: Path, config: ProjectConfig) -> tuple[str, Path]:
    """Create `.vdisplay/runs/{run_id}/` for one auto invocation."""
    base = ensure_metadata_layout(project, config)
    run_id = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    run_dir = base / "runs" / run_id
    (run_dir / "tasks").mkdir(parents=True, exist_ok=True)
    (run_dir / "observe").mkdir(parents=True, exist_ok=True)
    manifest = {
        "run_id": run_id,
        "started_at": _utc_now(),
        "project": str(project),
        "config_path": str(config.config_path) if config.config_path else None,
        "config": config.to_dict(),
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    latest = base / "latest-run.txt"
    latest.write_text(run_id + "\n", encoding="utf-8")
    return run_id, run_dir


def artifact_paths(config: ProjectConfig, *, task_id: str, kind: str = "observe") -> Path:
    """Stable path under `.vdisplay/observe/` for screenshots and sidecars."""
    safe_id = task_id.replace("/", "-")
    sub = config.metadata_dir / kind
    sub.mkdir(parents=True, exist_ok=True)
    return sub / safe_id


def copy_sidecar(src_png: Path, dest_png: Path, *, options: ConfigOptions | None = None) -> list[str]:
    copied: list[str] = []
    opts = options or get_runtime_options(dest_png.parent)

    def _copy_if_different(src: Path, dest: Path) -> None:
        if src.resolve() != dest.resolve():
            shutil.copy2(src, dest)

    _copy_if_different(src_png, dest_png)
    copied.append(str(dest_png))
    for suffix in opts.observe_sidecar_suffixes:
        sidecar = src_png.with_suffix(src_png.suffix + suffix)
        if sidecar.is_file():
            target = dest_png.with_suffix(dest_png.suffix + suffix)
            _copy_if_different(sidecar, target)
            copied.append(str(target))
            if suffix == ".context.json":
                ctx_base = dest_png.parent / "context"
                ctx_base.mkdir(parents=True, exist_ok=True)
                ctx_copy = ctx_base / target.name
                _copy_if_different(target, ctx_copy)
            if suffix == ".vql.json":
                vql_base = dest_png.parent / "vql"
                vql_base.mkdir(parents=True, exist_ok=True)
                vql_copy = vql_base / target.name
                _copy_if_different(target, vql_copy)
    return copied


def persist_task_result(
    run_dir: Path,
    *,
    task_id: str,
    payload: dict[str, Any],
    observe_paths: list[str] | None = None,
) -> Path:
    task_path = run_dir / "tasks" / f"{task_id}.json"
    record = {
        "task_id": task_id,
        "recorded_at": _utc_now(),
        "payload": payload,
        "observe_artifacts": observe_paths or [],
    }
    task_path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return task_path
