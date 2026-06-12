"""Markdown README generation for recorded vdisplay sessions."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .session_recorder import SessionDocument, StepRecord

_IMAGE_ARTIFACT_KINDS = frozenset(
    {"screenshot", "preview", "png", "observe", "diff", "before", "after", "verify"}
)


def _session_embed_images() -> bool:
    raw = os.environ.get("VDISPLAY_SESSION_EMBED_IMAGES", "1").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _is_image_artifact(kind: str, rel_path: str) -> bool:
    lowered = str(kind or "").lower()
    if lowered in _IMAGE_ARTIFACT_KINDS:
        return True
    suffix = Path(rel_path).suffix.lower()
    return suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def render_readme(doc: SessionDocument, *, session_dir: Path | None = None) -> str:
    lines = _render_header(doc)
    if session_dir is not None:
        lines.extend(_render_observe_section(session_dir))
    lines.extend(_render_step_toc(doc.steps))
    for step in doc.steps:
        lines.extend(_render_step_section(step))
    if doc.maps:
        lines.extend(_render_maps_section(doc.maps))
    return "\n".join(lines)


def _render_observe_section(session_dir: Path) -> list[str]:
    """Koru autonomy observe capture (separate from vdisplay step artifacts)."""
    capture = session_dir / "observe" / "capture.png"
    if not capture.is_file():
        return []
    rel = "observe/capture.png"
    lines = [
        "## Observe capture",
        "",
        f"- **File:** [{rel}]({rel})",
    ]
    if _session_embed_images():
        lines.extend(["", f"![observe capture]({rel})", ""])
    else:
        lines.append("")
    return lines


def _render_header(doc: SessionDocument) -> list[str]:
    return [
        f"# vdisplay session {doc.session_id}",
        "",
        "## Session metadata",
        "",
        "| Key | Value |",
        "|-----|-------|",
        f"| Session ID | `{doc.session_id}` |",
        f"| Started | `{doc.started_at}` |",
        f"| Updated | `{doc.updated_at}` |",
        f"| Source | `{doc.source}` |",
        f"| Route | `{doc.route_default}` |",
        f"| Host | `{doc.host}` |",
        f"| Steps | {doc.summary.get('total_steps', 0)} ({doc.summary.get('ok_steps', 0)} ok, {doc.summary.get('failed_steps', 0)} failed) |",
        "",
    ]


def _render_step_toc(steps: list[StepRecord]) -> list[str]:
    lines = ["## Steps", ""]
    for step in steps:
        title = step.verb.replace("_", " ")
        lines.append(f"- [Step {step.step_id} — {title}](#step-{step.step_id}--{title.lower().replace(' ', '-')})")
    lines.append("")
    return lines


def _render_step_section(step: StepRecord) -> list[str]:
    title = step.verb.replace("_", " ")
    lines = [
        f"## Step {step.step_id} — {title}",
        "",
        f"- **Time:** `{step.timestamp}` ({step.duration_ms} ms)",
        f"- **Source:** `{step.source}` · **Route:** `{step.route}`",
        f"- **Action:** `{step.action}` · **Result:** `{'ok' if step.ok else 'fail'}`",
    ]
    if step.command_line:
        lines.append(f"- **Command:** `{step.command_line}`")
    lines.extend(_render_step_routing(step))
    lines.extend(_render_step_verify(step))
    lines.extend(_render_step_files(step))
    lines.append("")
    return lines


def _render_step_routing(step: StepRecord) -> list[str]:
    lines: list[str] = []
    routing = step.diagnostics.get("routing") or (step.diagnostics.get("control") or {}).get("routing") or {}
    if routing.get("selected_provider"):
        lines.append(f"- **Backend:** `{routing.get('selected_provider')}`")
    if routing.get("why_selected"):
        lines.append(f"- **Routing:** {'; '.join(str(x) for x in routing.get('why_selected', [])[:3])}")
    control = step.diagnostics.get("control") or {}
    map_ctx = control.get("map")
    if isinstance(map_ctx, dict) and (map_ctx.get("path") or map_ctx.get("target")):
        lines.append(f"- **Map:** `{map_ctx.get('path')}` → target `{map_ctx.get('target')}`")
    if control.get("action_id"):
        lines.append(
            f"- **Lifecycle:** phase `{control.get('phase', '-')}` · "
            f"attempt `{control.get('attempt', 1)}` · id `{control.get('action_id')}`"
        )
    recovery = control.get("recovery_failed")
    if isinstance(recovery, dict) and recovery.get("reason"):
        lines.append(f"- **Recovery failed:** `{recovery.get('reason')}`")
    return lines


def _render_step_verify(step: StepRecord) -> list[str]:
    control = step.diagnostics.get("control") or {}
    verify = step.diagnostics.get("verify") or control.get("verify") or {}
    if not verify:
        return []
    lines = [
        f"- **Verify:** mode `{verify.get('verify_mode') or verify.get('mode', '-')}` · "
        f"verified `{verify.get('verified', '-')}`"
    ]
    if verify.get("confidence") is not None:
        lines.append(f"- **Confidence:** `{verify.get('confidence')}`")
    phases = verify.get("phases") or []
    if phases:
        lines.append(f"- **Verify phases:** {len(phases)}")
    return lines


def _render_step_files(step: StepRecord) -> list[str]:
    lines = [
        "- **Files:**",
        f"  - [{step.request_path}]({step.request_path})",
        f"  - [{step.result_path}]({step.result_path})",
        f"  - [diagnostics.json](steps/{step.step_id}/diagnostics.json)",
    ]
    embed = _session_embed_images()
    previews: list[str] = []
    for artifact in step.artifacts:
        rel = artifact.get("session_path")
        if rel:
            kind = artifact.get("kind", "artifact")
            lines.append(f"  - [{kind}]({rel})")
            if embed and _is_image_artifact(kind, rel):
                previews.append(f"![{kind}]({rel})")
    if previews:
        lines.append("- **Preview:**")
        for preview in previews:
            lines.append(f"  {preview}")
    return lines


def _render_maps_section(maps: list[dict[str, Any]]) -> list[str]:
    lines = ["## Maps", ""]
    for item in maps:
        rel = item.get("session_path")
        kind = item.get("kind", "map")
        source = item.get("source")
        if rel:
            line = f"- [{kind}]({rel})"
            if source:
                line += f" (from `{source}`)"
            lines.append(line)
    lines.append("")
    return lines
