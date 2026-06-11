"""Unified screen observation model — environment + pixels + analysis reuse."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class ScreenContext:
    """Portable snapshot of what vdisplay knows about one screen image."""

    version: int = 1
    image_path: str = ""
    capture: dict[str, Any] = field(default_factory=dict)
    environment: dict[str, Any] = field(default_factory=dict)
    vision: dict[str, Any] = field(default_factory=dict)
    map_pack: dict[str, Any] | None = None
    verify: dict[str, Any] = field(default_factory=dict)
    imgl: dict[str, Any] = field(default_factory=dict)
    vql: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)
    nl: str = ""
    fingerprint: str = ""
    observed_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if payload.get("map_pack") is None:
            payload.pop("map_pack", None)
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ScreenContext:
        return cls(
            version=int(payload.get("version", 1)),
            image_path=str(payload.get("image_path") or ""),
            capture=dict(payload.get("capture") or {}),
            environment=dict(payload.get("environment") or {}),
            vision=dict(payload.get("vision") or {}),
            map_pack=payload.get("map_pack"),
            verify=dict(payload.get("verify") or {}),
            imgl=dict(payload.get("imgl") or {}),
            vql=dict(payload.get("vql") or {}),
            artifacts=dict(payload.get("artifacts") or {}),
            nl=str(payload.get("nl") or ""),
            fingerprint=str(payload.get("fingerprint") or ""),
            observed_at=str(payload.get("observed_at") or datetime.now(UTC).isoformat()),
        )

    def merge_capture_meta(self, meta: dict[str, Any] | None) -> None:
        if not meta:
            return
        self.capture = {**self.capture, **meta}
        for key in ("display", "monitor", "source", "method"):
            if meta.get(key) is not None:
                self.environment.setdefault("capture", {})[key] = meta[key]

    def attach_diagnostics(self, diagnostics: dict[str, Any] | None) -> None:
        if not diagnostics:
            return
        control = diagnostics.get("control")
        if isinstance(control, dict):
            if control.get("routing"):
                self.environment["routing"] = control["routing"]
            if control.get("map"):
                self.environment["map"] = control["map"]
            if control.get("verify"):
                self.verify = {**self.verify, **control["verify"]}
            if control.get("actuation"):
                self.vision["actuation"] = control["actuation"]
        routing = diagnostics.get("routing")
        if isinstance(routing, dict):
            self.environment.setdefault("routing", routing)
        verify = diagnostics.get("verify")
        if isinstance(verify, dict):
            self.verify = {**self.verify, **verify}

    def attach_map_path(self, map_path: str | Path | None) -> None:
        if not map_path:
            return
        path = Path(map_path).expanduser()
        if not path.is_file():
            return
        try:
            from ..control.gui_map import load_gui_map

            pack = load_gui_map(path)
            self.map_pack = pack.to_dict() if hasattr(pack, "to_dict") else asdict(pack)
            self.environment["map_path"] = str(path.resolve())
            self.artifacts.setdefault("map", str(path.resolve()))
        except Exception as exc:
            self.environment["map_error"] = str(exc)

    def compute_fingerprint(self) -> str:
        path = Path(self.image_path).expanduser()
        if path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
        else:
            digest = hashlib.sha256(json.dumps(self.capture, sort_keys=True).encode()).hexdigest()[:16]
        self.fingerprint = digest
        return digest

    def sidecar_path(self, suffix: str = ".context.json") -> Path:
        path = Path(self.image_path).expanduser()
        return path.with_suffix(path.suffix + suffix)

    def write_sidecar(self) -> Path:
        out = self.sidecar_path()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        self.artifacts["context"] = str(out.resolve())
        return out


def screen_context_from_capture(
    payload: dict[str, Any],
    *,
    image_path: str | None = None,
    diagnostics: dict[str, Any] | None = None,
    map_path: str | None = None,
) -> ScreenContext:
    path = image_path or payload.get("path") or payload.get("saved") or ""
    ctx = ScreenContext(image_path=str(path))
    ctx.merge_capture_meta(payload)
    ctx.attach_diagnostics(diagnostics)
    ctx.attach_map_path(map_path)
    if payload.get("nl"):
        ctx.nl = str(payload["nl"])
    if payload.get("img2nl"):
        ctx.imgl["img2nl"] = payload["img2nl"]
        img2nl = payload["img2nl"]
        if isinstance(img2nl, dict) and img2nl.get("ok"):
            meta = img2nl.get("metadata") or {}
            scene = meta.get("scene") if isinstance(meta, dict) else None
            if isinstance(scene, dict):
                ctx.imgl.setdefault("ok", True)
                ctx.imgl.setdefault("scene", scene)
                ctx.imgl.setdefault("source", img2nl.get("source") or "imgl")
    if payload.get("vision_llm"):
        ctx.vision["llm"] = payload["vision_llm"]
    if payload.get("preview") and isinstance(payload["preview"], dict):
        ctx.vision["preview"] = payload["preview"]
    ctx.compute_fingerprint()
    return ctx


def load_environment_snapshot(*, display: str | None = None) -> dict[str, Any]:
    """Best-effort monitors/windows/platform for VQL metadata.environment."""
    env: dict[str, Any] = {"display": display}
    try:
        from ..control.descriptors import detect_platform_profile

        profile = detect_platform_profile()
        env["platform"] = {
            "host_environment": profile.host_environment.value,
            "session_type": profile.session_type,
        }
    except Exception:
        pass
    try:
        from ..discovery import list_monitors, list_windows

        env["monitors"] = list_monitors(display=display)
        env["windows"] = list_windows(display=display, apps_only=True)
    except Exception:
        pass
    return env
