"""Backend reliability projection and routing priors."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from ..event_store import EventStore
from ..events import DomainEvent

_SCORE_EVENT_TYPES = frozenset(
    {
        "CommandCompleted",
        "StepRecorded",
        "ControlVerificationPassed",
        "ControlVerificationFailed",
        "ControlActionPlanned",
        "BackendScoreUpdated",
    }
)


def _score_bucket(
    scores: dict[str, dict[str, dict[str, int]]],
    *,
    profile: str,
    provider: str,
) -> dict[str, int]:
    return scores.setdefault(profile, {}).setdefault(
        str(provider),
        {"success": 0, "fail": 0, "score": 50},
    )


def _apply_outcome(bucket: dict[str, int], *, success: bool) -> None:
    if success:
        bucket["success"] += 1
    else:
        bucket["fail"] += 1
    total = bucket["success"] + bucket["fail"]
    bucket["score"] = int(round(100 * bucket["success"] / total)) if total else 50


def _routing_from_event(event: DomainEvent) -> tuple[str | None, str | None, dict[str, Any] | None]:
    body = event.body or {}
    diagnostics = body.get("diagnostics") if isinstance(body.get("diagnostics"), dict) else {}
    control = diagnostics.get("control") if isinstance(diagnostics.get("control"), dict) else {}
    routing = control.get("routing") if isinstance(control.get("routing"), dict) else body.get("routing")
    if not isinstance(routing, dict):
        routing = diagnostics.get("routing") if isinstance(diagnostics.get("routing"), dict) else None
    if not isinstance(routing, dict):
        return None, None, None
    provider = routing.get("selected_provider")
    if not provider:
        return None, None, None
    profile = str(routing.get("application_profile") or "default")
    verify = control.get("verify") if isinstance(control.get("verify"), dict) else diagnostics.get("verify")
    return profile, str(provider), verify if isinstance(verify, dict) else None


def build_backend_scores(events: list[DomainEvent]) -> dict[str, Any]:
    scores: dict[str, dict[str, dict[str, int]]] = {}
    for event in events:
        if event.event_type not in _SCORE_EVENT_TYPES:
            continue

        if event.event_type == "BackendScoreUpdated":
            profile = str(event.body.get("application_profile") or event.body.get("app_profile") or "default")
            provider = str(event.body.get("provider") or "")
            if not provider:
                continue
            bucket = _score_bucket(scores, profile=profile, provider=provider)
            delta = event.body.get("delta")
            if isinstance(delta, dict):
                bucket["success"] += int(delta.get("success") or 0)
                bucket["fail"] += int(delta.get("fail") or 0)
            elif event.body.get("success") is True:
                bucket["success"] += 1
            elif event.body.get("success") is False:
                bucket["fail"] += 1
            total = bucket["success"] + bucket["fail"]
            bucket["score"] = int(round(100 * bucket["success"] / total)) if total else 50
            continue

        profile, provider, verify = _routing_from_event(event)
        if not profile or not provider:
            continue
        if event.event_type == "ControlActionPlanned" and verify is None:
            continue
        bucket = _score_bucket(scores, profile=profile, provider=provider)
        verified = verify.get("verified") if verify else None
        ok = bool(event.body.get("ok", True))
        if event.event_type == "ControlVerificationPassed" or (ok and verified is not False):
            _apply_outcome(bucket, success=True)
        elif event.event_type == "ControlVerificationFailed" or not ok or verified is False:
            _apply_outcome(bucket, success=False)
    return scores


def global_backend_scores_path() -> Path:
    config_root = os.environ.get("XDG_CONFIG_HOME", "").strip()
    if not config_root:
        config_root = str(Path.home() / ".config")
    return Path(config_root).expanduser() / "vdisplay" / "backend_scores.json"


def load_global_backend_scores() -> dict[str, Any]:
    path = global_backend_scores_path()
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def load_session_backend_scores(session_root: Path | None) -> dict[str, Any]:
    if session_root is None or not session_root.is_dir():
        return {}
    path = session_root / "projections" / "backend_scores.json"
    if path.is_file():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except (OSError, json.JSONDecodeError):
            pass
    return build_backend_scores(EventStore(session_root).read_all())


def merge_backend_scores(*sources: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, dict[str, dict[str, int]]] = {}
    for source in sources:
        if not isinstance(source, dict):
            continue
        for profile, providers in source.items():
            if not isinstance(providers, dict):
                continue
            for provider, bucket in providers.items():
                if not isinstance(bucket, dict):
                    continue
                target = _score_bucket(merged, profile=str(profile), provider=str(provider))
                target["success"] += int(bucket.get("success") or 0)
                target["fail"] += int(bucket.get("fail") or 0)
                total = target["success"] + target["fail"]
                target["score"] = int(round(100 * target["success"] / total)) if total else 50
    return merged


def resolve_active_session_root() -> Path | None:
    explicit = os.environ.get("VDISPLAY_SESSION_DIR", "").strip()
    if explicit:
        path = Path(explicit).expanduser()
        return path if path.is_dir() else None
    try:
        from ..session_recorder import _current_recorder

        recorder = _current_recorder.get()
        if recorder is not None:
            return recorder.session_dir
    except Exception:
        pass
    return None


def load_merged_backend_scores(*, session_root: Path | None = None) -> dict[str, Any]:
    session_root = session_root or resolve_active_session_root()
    return merge_backend_scores(
        load_global_backend_scores(),
        load_session_backend_scores(session_root),
    )


def provider_score_prior(
    provider: str,
    *,
    application_profile: str | None,
    scores: dict[str, Any] | None = None,
) -> tuple[float, list[str]]:
    """Return routing score boost from historical backend reliability (prior, not override)."""
    profile = application_profile or "default"
    merged = scores if scores is not None else load_merged_backend_scores()
    providers = merged.get(profile) if isinstance(merged.get(profile), dict) else merged.get("default")
    if not isinstance(providers, dict):
        return 0.0, []
    bucket = providers.get(provider)
    if not isinstance(bucket, dict):
        return 0.0, []

    score = int(bucket.get("score") or 50)
    success = int(bucket.get("success") or 0)
    fail = int(bucket.get("fail") or 0)
    total = success + fail
    if total <= 0:
        return 0.0, []

    boost = (score - 50) * 1.5
    if total < 3:
        boost *= total / 3.0
    reasons = [f"backend score prior {score} ({success}/{total} verified ok)"]
    return boost, reasons


def load_backend_scores(session_root: Path) -> dict[str, Any]:
    path = session_root / "projections" / "backend_scores.json"
    if not path.is_file():
        return build_backend_scores(EventStore(session_root).read_all())
    return json.loads(path.read_text(encoding="utf-8"))
