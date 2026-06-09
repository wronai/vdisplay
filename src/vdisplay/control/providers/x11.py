"""X11 pointer-injection fallback control provider."""

from __future__ import annotations

import os
from typing import Any

from ...discovery import resolve_host_display
from ...exceptions import VDisplayError
from ...input.linux_xdotool import LinuxXdotoolInput
from ..base import ControlProvider
from ..models import ControlBounds, ControlNode, ControlRole, ControlSnapshot
from ..selector import ControlSelector, find_matches, pick_match


class X11ControlProvider(ControlProvider):
    name = "x11-fallback"

    def __init__(self, *, display: str | None = None) -> None:
        self.display = resolve_host_display(display or os.environ.get("DISPLAY"))
        self._cache: ControlSnapshot | None = None
        self._input = LinuxXdotoolInput(self.display)

    def available(self) -> tuple[bool, str]:
        try:
            from ...utils import require_command

            require_command("xdotool")
            return True, "xdotool pointer injection"
        except Exception as exc:
            return False, str(exc)

    def snapshot(
        self,
        *,
        window_id: str | None = None,
        app: str | None = None,
        max_depth: int = 8,
    ) -> ControlSnapshot:
        from ...windows import find_windows, pick_best_window

        matches = find_windows(
            self.display,
            match_app=app,
            apps_only=True,
        )
        if window_id:
            matches = [item for item in matches if str(item.get("window_id")) == str(window_id)]
        window = pick_best_window(matches)
        if window is None:
            hint = "x11 fallback: no window matched for snapshot"
            if app:
                hint += f" (app={app!r})"
            from ...discovery import window_discovery_meta

            meta = window_discovery_meta(self.display)
            if meta.get("session_type") == "wayland":
                hint += (
                    ". Session is Wayland — native apps like Firefox are invisible to xdotool;"
                    " use --backend atspi, a browser session, or MOZ_ENABLE_WAYLAND=0 for X11 Firefox"
                )
            else:
                hint += ". Run: vdisplay windows --apps-only"
            raise VDisplayError(hint)

        node_id = f"x11:{window['window_id']}"
        bounds = ControlBounds(
            x=int(window.get("x") or 0),
            y=int(window.get("y") or 0),
            width=int(window.get("width") or 0),
            height=int(window.get("height") or 0),
        )
        node = ControlNode(
            id=node_id,
            backend=self.name,
            role=ControlRole.WINDOW,
            name=str(window.get("title") or window.get("name") or ""),
            bounds=bounds,
            window_id=str(window.get("window_id")),
            app_label=str(window.get("app_label") or ""),
        )
        snapshot = ControlSnapshot(
            backend=self.name,
            window_id=str(window.get("window_id")),
            app_label=str(window.get("app_label") or ""),
            nodes={node_id: node},
            root_ids=[node_id],
        )
        self._cache = snapshot
        return snapshot

    def find(self, selector: ControlSelector) -> list[ControlNode]:
        snapshot = self._cache or self.snapshot(
            app=selector.app,
            window_id=selector.window_id,
        )
        return find_matches(snapshot.nodes, selector)

    def _node_for(self, element_id: str) -> ControlNode:
        snapshot = self._cache
        if snapshot is None or element_id not in snapshot.nodes:
            raise VDisplayError(f"x11 fallback: unknown element {element_id}")
        return snapshot.nodes[element_id]

    def _click_node(self, node: ControlNode) -> dict[str, Any]:
        if node.bounds is None:
            raise VDisplayError(f"x11 fallback: no bounds for {node.id}")
        cx, cy = node.bounds.center
        self._input.move(cx, cy)
        self._input.click(1)
        return {"ok": True, "element_id": node.id, "backend": self.name, "method": "click"}

    def invoke(self, element_id: str, *, action: str | None = None) -> dict[str, Any]:
        return self._click_node(self._node_for(element_id))

    def focus(self, element_id: str) -> dict[str, Any]:
        node = self._node_for(element_id)
        if node.bounds is None:
            raise VDisplayError(f"x11 fallback: no bounds for {node.id}")
        cx, cy = node.bounds.center
        self._input.move(cx, cy)
        self._input.click(1)
        return {"ok": True, "element_id": node.id, "backend": self.name, "method": "focus-click"}

    def set_value(self, element_id: str, value: str) -> dict[str, Any]:
        self.focus(element_id)
        self._input.type_text(value)
        return {"ok": True, "element_id": element_id, "backend": self.name, "method": "type"}

    def bounds(self, element_id: str) -> ControlBounds | None:
        node = self._node_for(element_id)
        return node.bounds
