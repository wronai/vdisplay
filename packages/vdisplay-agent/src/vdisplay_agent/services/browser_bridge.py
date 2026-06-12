"""Browser/Electron pushed frame store for vdisplay-agent."""

from __future__ import annotations

import base64
import os
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from vdisplay.exceptions import VDisplayError

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _display_key(display: str | None) -> str:
    return str(display or os.environ.get("DISPLAY") or ":0")


def _safe_part(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in value) or "default"


def _max_frame_bytes() -> int:
    raw = os.environ.get("VDISPLAY_BROWSER_BRIDGE_MAX_FRAME_MB", "25")
    try:
        return max(1, int(float(raw))) * 1024 * 1024
    except (TypeError, ValueError):
        return 25 * 1024 * 1024


def _ttl_s(raw: Any = None) -> float:
    value = raw if raw is not None else os.environ.get("VDISPLAY_BROWSER_BRIDGE_TTL_S", "5")
    try:
        return max(0.5, min(60.0, float(value)))
    except (TypeError, ValueError):
        return 5.0


def _dict_or_none(value: Any) -> dict[str, Any] | None:
    return dict(value) if isinstance(value, dict) else None


@dataclass
class BrowserFrameEntry:
    bridge_id: str
    source: str
    display: str
    path: Path
    meta: dict[str, Any]
    received_at: float


@dataclass
class BrowserBridgeState:
    bridge_id: str
    client: str
    version: str
    sources: list[str]
    display: str
    ttl_s: float
    registered_at: float = field(default_factory=time.monotonic)
    heartbeat_at: float = field(default_factory=time.monotonic)
    sharing: bool = False
    fps: float | None = None


class BrowserFrameStore:
    """In-memory index plus temp PNG files for browser-pushed frames."""

    def __init__(self) -> None:
        self.bridge: BrowserBridgeState | None = None
        self.frames: dict[tuple[str, str], BrowserFrameEntry] = {}

    def clear(self) -> None:
        for entry in list(self.frames.values()):
            try:
                entry.path.unlink(missing_ok=True)
            except Exception:
                pass
        self.frames.clear()
        self.bridge = None

    def _maybe_expire_bridge(self) -> None:
        bridge = self.bridge
        if bridge is None:
            return
        stale_after = max(bridge.ttl_s * 2.0, bridge.ttl_s + 1.0)
        if (time.monotonic() - bridge.heartbeat_at) > stale_after:
            self.clear()

    def register(self, body: dict[str, Any]) -> dict[str, Any]:
        sources = _sources_from_body(body)
        bridge_id = f"bb_{uuid.uuid4().hex[:12]}"
        self.bridge = BrowserBridgeState(
            bridge_id=bridge_id,
            client=str(body.get("client") or "browser-bridge"),
            version=str(body.get("version") or ""),
            sources=sources,
            display=_display_key(body.get("display")),
            ttl_s=_ttl_s(body.get("ttl_s")),
        )
        return {
            "ok": True,
            "bridge_id": bridge_id,
            "ttl_s": self.bridge.ttl_s,
            "ingest_url": "/capture/ingest",
            "heartbeat_url": "/session/browser-bridge/heartbeat",
            "sources": list(self.bridge.sources),
            "monitors": list(self.bridge.sources),
            "keeper_mode": "browser_bridge",
        }

    def heartbeat(self, body: dict[str, Any]) -> dict[str, Any]:
        self._maybe_expire_bridge()
        bridge = self._require_bridge(body.get("bridge_id"))
        sources = _sources_from_body(body)
        if sources:
            bridge.sources = sources
        bridge.sharing = bool(body.get("sharing"))
        try:
            bridge.fps = float(body.get("fps")) if body.get("fps") is not None else bridge.fps
        except (TypeError, ValueError):
            pass
        bridge.heartbeat_at = time.monotonic()
        return {
            "ok": True,
            "bridge_id": bridge.bridge_id,
            "capture_ready": self.capture_ready(),
            "keeper_mode": "browser_bridge",
        }

    def ingest(self, body: dict[str, Any]) -> dict[str, Any]:
        self._maybe_expire_bridge()
        bridge = self._require_bridge(body.get("bridge_id"))
        source = str(body.get("source") or (bridge.sources[0] if bridge.sources else "default")).strip()
        if not source:
            raise VDisplayError("source required")
        if bridge.sources and source not in bridge.sources:
            raise VDisplayError(f"source {source!r} was not registered for this bridge")
        png = _png_bytes_from_body(body)
        if len(png) > _max_frame_bytes():
            raise VDisplayError(f"frame too large: {len(png)} bytes")
        if not png.startswith(_PNG_MAGIC):
            raise VDisplayError("ingest accepts PNG frames only")

        display = _display_key(body.get("display") or bridge.display)
        directory = Path(tempfile.gettempdir()) / "vdisplay-browser-bridge" / bridge.bridge_id
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{_safe_part(display)}__{_safe_part(source)}.png"
        path.write_bytes(png)
        now = time.monotonic()
        meta = {
            "method": "browser-bridge",
            "keeper_mode": "browser_bridge",
            "bridge_id": bridge.bridge_id,
            "client": bridge.client,
            "source": source,
            "monitor_name": source,
            "display": display,
            "seq": body.get("seq"),
            "mime": "image/png",
            "width": _int_or_none(body.get("width")),
            "height": _int_or_none(body.get("height")),
            "captured_at_ms": _int_or_none(body.get("captured_at_ms")),
            "display_id": body.get("display_id"),
            "display_label": body.get("display_label"),
            "source_id": body.get("source_id"),
            "source_name": body.get("source_name"),
            "display_bounds": _dict_or_none(body.get("display_bounds")),
            "source_bounds": _dict_or_none(body.get("source_bounds")),
            "scale_factor": body.get("scale_factor"),
        }
        self.frames[(display, f"{bridge.bridge_id}:{source}")] = BrowserFrameEntry(
            bridge_id=bridge.bridge_id,
            source=source,
            display=display,
            path=path,
            meta={k: v for k, v in meta.items() if v is not None},
            received_at=now,
        )
        bridge.sharing = True
        bridge.heartbeat_at = now
        return {
            "ok": True,
            "bridge_id": bridge.bridge_id,
            "source": source,
            "bytes": len(png),
            "seq": body.get("seq"),
            "age_ms": 0,
            "capture_ready": self.capture_ready(),
        }

    def status(self) -> dict[str, Any]:
        self._maybe_expire_bridge()
        bridge = self.bridge
        if bridge is None:
            return {
                "ok": True,
                "registered": False,
                "sharing": False,
                "capture_ready": False,
                "keeper_mode": "browser_bridge",
                "monitors": {},
            }
        now = time.monotonic()
        monitors: dict[str, dict[str, Any]] = {}
        for (display, _key), entry in sorted(self.frames.items()):
            if display != bridge.display:
                continue
            age_ms = int((now - entry.received_at) * 1000)
            source = entry.source
            existing = monitors.get(source)
            if existing and int(existing.get("age_ms") or 0) <= age_ms:
                continue
            monitors[source] = {
                "last_seq": entry.meta.get("seq"),
                "age_ms": age_ms,
                "bytes": entry.path.stat().st_size if entry.path.is_file() else 0,
                "fresh": self._entry_fresh(entry),
                "path": str(entry.path),
                "width": entry.meta.get("width"),
                "height": entry.meta.get("height"),
                "display_id": entry.meta.get("display_id"),
                "display_label": entry.meta.get("display_label"),
                "source_name": entry.meta.get("source_name"),
                "display_bounds": entry.meta.get("display_bounds"),
            }
        return {
            "ok": True,
            "registered": True,
            "bridge_id": bridge.bridge_id,
            "client": bridge.client,
            "version": bridge.version,
            "sharing": bridge.sharing,
            "capture_ready": self.capture_ready(),
            "keeper_mode": "browser_bridge",
            "sources": list(bridge.sources),
            "monitors": monitors,
            "ttl_s": bridge.ttl_s,
            "heartbeat_age_ms": int((now - bridge.heartbeat_at) * 1000),
            "last_frame_age_ms": _min_fresh_frame_age_ms(monitors),
            "fps": bridge.fps,
        }

    def capture_ready(self) -> bool:
        bridge = self.bridge
        if bridge is None:
            return any(self._entry_fresh(entry) for entry in self.frames.values())
        if bridge.sources:
            return all(self.get_fresh(source=source, display=bridge.display) is not None for source in bridge.sources)
        return any(self._entry_fresh(entry) for entry in self.frames.values())

    def get_fresh(
        self,
        *,
        source: str | None = None,
        display: str | None = None,
    ) -> BrowserFrameEntry | None:
        bridge = self.bridge
        if bridge is None:
            return None
        display_name = _display_key(display or bridge.display)
        wanted = str(source or "").strip()
        if wanted and wanted.lower() not in {"primary", "default"}:
            fresh = [
                entry
                for (entry_display, _key), entry in self.frames.items()
                if entry_display == display_name and entry.source == wanted and self._entry_fresh(entry)
            ]
            if not fresh:
                return None
            fresh.sort(key=lambda item: item.received_at, reverse=True)
            return fresh[0]
        fresh = [
            entry
            for (entry_display, _key), entry in self.frames.items()
            if entry_display == display_name and self._entry_fresh(entry)
        ]
        if not fresh:
            return None
        fresh.sort(key=lambda item: item.received_at, reverse=True)
        return fresh[0]

    def copy_fresh(
        self,
        output: str | Path,
        *,
        source: str | None = None,
        display: str | None = None,
        region: tuple[int, int, int, int] | None = None,
    ) -> dict[str, Any] | None:
        entry = self.get_fresh(source=source, display=display)
        if entry is None:
            return None
        data = entry.path.read_bytes()
        meta = dict(entry.meta)
        if region is not None:
            from vdisplay.capture.linux_xwd import _crop_png, is_blank_png

            data = _crop_png(data, region)
            if is_blank_png(data):
                raise VDisplayError(f"browser bridge crop blank for source {entry.source}")
            meta["region"] = {"x": region[0], "y": region[1], "width": region[2], "height": region[3]}
            meta["browser_bridge_crop"] = "requested-region"
        out = Path(output).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        meta.update(
            {
                "path": str(out.resolve()),
                "bytes": len(data),
                "age_ms": int((time.monotonic() - entry.received_at) * 1000),
            }
        )
        return meta

    def copy_all_fresh(
        self,
        output_dir: str | Path,
        *,
        display: str | None = None,
    ) -> list[dict[str, Any]]:
        bridge = self.bridge
        if bridge is None:
            return []
        display_name = _display_key(display or bridge.display)
        out_dir = Path(output_dir).expanduser()
        out_dir.mkdir(parents=True, exist_ok=True)
        captures: list[dict[str, Any]] = []
        for (entry_display, _key), entry in sorted(self.frames.items()):
            if entry_display != display_name or not self._entry_fresh(entry):
                continue
            source = entry.source
            meta = self.copy_fresh(out_dir / f"{source}.png", source=source, display=display_name)
            if meta is not None:
                captures.append(meta)
        return captures

    def _entry_fresh(self, entry: BrowserFrameEntry) -> bool:
        bridge = self.bridge
        ttl = bridge.ttl_s if bridge is not None else _ttl_s()
        return entry.path.is_file() and (time.monotonic() - entry.received_at) <= ttl

    def _require_bridge(self, bridge_id: Any) -> BrowserBridgeState:
        bridge = self.bridge
        if bridge is None:
            raise VDisplayError("browser bridge not registered")
        if str(bridge_id or "") != bridge.bridge_id:
            raise VDisplayError("unknown browser bridge_id")
        return bridge


def _sources_from_body(body: dict[str, Any]) -> list[str]:
    raw = body.get("sources")
    if raw is None:
        raw = body.get("monitors")
    if raw is None and body.get("source") is not None:
        raw = [body.get("source")]
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        return []
    sources: list[str] = []
    for item in raw:
        text = str(item or "").strip()
        if text and text not in sources:
            sources.append(text)
    return sources


def _png_bytes_from_body(body: dict[str, Any]) -> bytes:
    raw = str(body.get("png_base64") or body.get("data_base64") or "")
    data_url = str(body.get("data_url") or "")
    if not raw and data_url:
        marker = "base64,"
        index = data_url.find(marker)
        raw = data_url[index + len(marker) :] if index >= 0 else data_url
    if not raw:
        raise VDisplayError("png_base64 required")
    try:
        return base64.b64decode(raw, validate=True)
    except Exception as exc:
        raise VDisplayError("png_base64 is invalid") from exc


def _min_fresh_frame_age_ms(monitors: dict[str, dict[str, Any]]) -> int | None:
    ages = [int(item["age_ms"]) for item in monitors.values() if item.get("fresh") and item.get("age_ms") is not None]
    return min(ages) if ages else None


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def register_browser_bridge(store: Any, body: dict[str, Any]) -> dict[str, Any]:
    return store.browser_bridge.register(dict(body or {}))


def heartbeat_browser_bridge(store: Any, body: dict[str, Any]) -> dict[str, Any]:
    return store.browser_bridge.heartbeat(dict(body or {}))


def browser_bridge_status(store: Any) -> dict[str, Any]:
    return store.browser_bridge.status()


def ingest_browser_frame(store: Any, body: dict[str, Any]) -> dict[str, Any]:
    return store.browser_bridge.ingest(dict(body or {}))
