"""Linux AT-SPI2 semantic control provider."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from ...exceptions import VDisplayError
from ..base import ControlProvider
from ..models import ControlBounds, ControlNode, ControlRole, ControlSnapshot
from ..selector import ControlSelector, find_matches

_ROLE_MAP = {
    "push button": ControlRole.BUTTON,
    "entry": ControlRole.INPUT,
    "text": ControlRole.INPUT,
}


def _gi_available() -> bool:
    try:
        import gi

        gi.require_version("Atspi", "2.0")
        from gi.repository import Atspi  # noqa: F401

        return True
    except ImportError:
        return False


def _system_python() -> str:
    for candidate in ("/usr/bin/python3", shutil.which("python3")):
        if candidate and Path(candidate).is_file():
            return candidate
    return sys.executable


def _vdisplay_src_path() -> Path:
    import vdisplay

    root = Path(vdisplay.__file__).resolve().parent
    return root.parent if root.name == "vdisplay" and (root.parent / "vdisplay").is_dir() else root


def _run_subprocess(payload: dict[str, Any]) -> dict[str, Any]:
    src_path = _vdisplay_src_path()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(src_path) + os.pathsep + env.get("PYTHONPATH", "")
    script = r'''
import json, sys
from vdisplay.control.providers.atspi_impl import dispatch
payload = json.loads(sys.argv[1])
try:
    result = dispatch(payload)
    print(json.dumps({"ok": True, **result}))
except Exception as exc:
    print(json.dumps({"ok": False, "error": str(exc)}))
'''
    completed = subprocess.run(
        [_system_python(), "-c", script, json.dumps(payload)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
        env=env,
    )
    try:
        result = json.loads((completed.stdout or "").strip() or "{}")
    except json.JSONDecodeError as exc:
        err = (completed.stderr or completed.stdout or "atspi subprocess failed").strip()
        raise VDisplayError(err) from exc
    if not result.get("ok"):
        raise VDisplayError(str(result.get("error") or "atspi subprocess failed"))
    return result


def _snapshot_from_dict(data: dict[str, Any]) -> ControlSnapshot:
    nodes: dict[str, ControlNode] = {}
    for node_id, raw in (data.get("nodes") or {}).items():
        bounds = None
        if raw.get("bounds"):
            b = raw["bounds"]
            bounds = ControlBounds(int(b["x"]), int(b["y"]), int(b["width"]), int(b["height"]))
        nodes[node_id] = ControlNode(
            id=raw["id"],
            backend=raw.get("backend", "atspi"),
            role=ControlRole(raw.get("role", "unknown")),
            name=raw.get("name"),
            description=raw.get("description"),
            bounds=bounds,
            window_id=raw.get("window_id"),
            app_label=raw.get("app_label"),
            state=raw.get("state") or {},
            text_value=raw.get("text_value"),
            parent_id=raw.get("parent_id"),
            children_ids=list(raw.get("children_ids") or []),
        )
    return ControlSnapshot(
        backend=data.get("backend", "atspi"),
        window_id=data.get("window_id"),
        app_label=data.get("app_label"),
        nodes=nodes,
        root_ids=list(data.get("root_ids") or []),
    )


class AtspiControlProvider(ControlProvider):
    name = "atspi"

    def __init__(self) -> None:
        self._cache: ControlSnapshot | None = None
        self._use_subprocess = not _gi_available()

    def available(self) -> tuple[bool, str]:
        if not self._use_subprocess:
            try:
                from .atspi_impl import dispatch

                result = dispatch({"op": "available"})
                return bool(result.get("ok")), str(result.get("reason") or "AT-SPI2 bus active")
            except Exception as exc:
                return False, str(exc)
        try:
            result = _run_subprocess({"op": "available"})
            return True, str(result.get("reason") or "AT-SPI2 bus active (system python)")
        except VDisplayError as exc:
            return False, str(exc)

    def snapshot(
        self,
        *,
        window_id: str | None = None,
        app: str | None = None,
        max_depth: int = 8,
    ) -> ControlSnapshot:
        params = {"window_id": window_id, "app": app, "max_depth": max_depth}
        if not self._use_subprocess:
            from .atspi_impl import snapshot_dict

            snapshot = _snapshot_from_dict(snapshot_dict(**params))
        else:
            result = _run_subprocess({"op": "snapshot", "params": params})
            snapshot = _snapshot_from_dict(result["snapshot"])
        self._cache = snapshot
        return snapshot

    def find(self, selector: ControlSelector) -> list[ControlNode]:
        snapshot = self._cache or self.snapshot(
            app=selector.app,
            window_id=selector.window_id,
        )
        return find_matches(snapshot.nodes, selector)

    def invoke(self, element_id: str, *, action: str | None = None) -> dict[str, Any]:
        payload = {"op": "invoke", "element_id": element_id, "action": action}
        if not self._use_subprocess:
            from .atspi_impl import dispatch

            return dispatch(payload)
        return _run_subprocess(payload)

    def focus(self, element_id: str) -> dict[str, Any]:
        payload = {"op": "focus", "element_id": element_id}
        if not self._use_subprocess:
            from .atspi_impl import dispatch

            return dispatch(payload)
        return _run_subprocess(payload)

    def set_value(self, element_id: str, value: str) -> dict[str, Any]:
        payload = {"op": "set_value", "element_id": element_id, "value": value}
        if not self._use_subprocess:
            from .atspi_impl import dispatch

            return dispatch(payload)
        return _run_subprocess(payload)

    def bounds(self, element_id: str) -> ControlBounds | None:
        snapshot = self._cache or self.snapshot()
        node = snapshot.nodes.get(element_id)
        return node.bounds if node else None
