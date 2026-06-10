"""Vision-only surface provider — OCR, template, and spatial anchor find/invoke (PR-20/22)."""

from __future__ import annotations

import os
import shutil
import time
from typing import Any, Callable

from ....exceptions import VDisplayError
from ...base import ControlProvider
from ...models import ControlBounds, ControlNode, ControlRole, ControlSnapshot
from ...screenshot_verify import capture_control_screenshot
from ...selector import ControlSelector
from ...vision_ocr import (
    OcrTextBox,
    anchor_spatial_find,
    ocr_anchor_combined_find,
    ocr_available,
    ocr_find_selector,
)
from ...vision_template import (
    TemplateMatch,
    load_template_png,
    match_template,
    template_available,
    template_find_selector,
)
from ...action_bounds import action_bounds_for_vision
from ...vision_disambiguate import disambiguation_meta, resolve_vision_matches
from ...vision_preview import PreviewMatch, VisionPreviewDebug

CaptureFn = Callable[..., tuple[bytes, dict[str, Any]]]
PointerClickFn = Callable[[int, int], None]
PointerTypeFn = Callable[[str], None]


class VisionStubProvider(ControlProvider):
    """Canvas/game/stream surfaces — semantic tree unavailable; OCR/template + pointer invoke."""

    name = "vision"

    def __init__(
        self,
        *,
        display: str | None = None,
        session_id: str | None = None,
        capture_fn: CaptureFn | None = None,
        pointer_click: PointerClickFn | None = None,
        pointer_type: PointerTypeFn | None = None,
    ) -> None:
        self.display = display
        self.session_id = session_id
        self._capture_fn = capture_fn
        self._pointer_click = pointer_click
        self._pointer_type = pointer_type
        self._cache: ControlSnapshot | None = None
        self._last_ocr_boxes: list[OcrTextBox] = []
        self._last_capture: tuple[bytes, dict[str, Any]] | None = None
        self._preview_debug_enabled: bool = False
        self._last_find_debug: VisionPreviewDebug | None = None

    def available(self) -> tuple[bool, str]:
        ocr_ready, ocr_reason = ocr_available()
        template_ready, template_reason = template_available()
        if ocr_ready and template_ready:
            return True, f"vision OCR + template ({ocr_reason}; {template_reason})"
        if ocr_ready:
            return True, f"vision OCR ({ocr_reason})"
        if template_ready:
            return True, f"vision template ({template_reason})"
        return True, "vision stub (OCR/template deps missing — find/invoke return structured errors)"

    def _capture_png(self, *, target: ControlNode | None = None) -> tuple[bytes, dict[str, Any]]:
        if self._capture_fn is not None:
            payload = self._capture_fn(display=self.display)
        else:
            payload = capture_control_screenshot(display=self.display, target=target, capture_fn=None)
        self._last_capture = payload
        return payload

    def last_capture(self) -> tuple[bytes, dict[str, Any]] | None:
        return self._last_capture

    def last_find_debug(self) -> VisionPreviewDebug | None:
        return self._last_find_debug

    def enable_preview_debug(self, enabled: bool = True) -> None:
        self._preview_debug_enabled = enabled

    @staticmethod
    def _box_key(box: OcrTextBox) -> tuple[str, int, int]:
        return (box.text, box.bounds.x, box.bounds.y)

    def _record_find_debug(
        self,
        *,
        selector: ControlSelector,
        raw_count: int,
        filtered_count: int,
        rejected_boxes: list[OcrTextBox] | None = None,
        rejected_nodes: list[ControlNode] | None = None,
    ) -> None:
        if not self._preview_debug_enabled:
            self._last_find_debug = None
            return
        rejected: list[PreviewMatch] = []
        if rejected_boxes:
            for index, box in enumerate(rejected_boxes[:20]):
                rejected.append(
                    PreviewMatch(
                        index=index,
                        bounds=box.bounds,
                        label=box.text[:48],
                        confidence=box.confidence,
                        kind="ocr",
                        rejected=True,
                    )
                )
        if rejected_nodes:
            for index, node in enumerate(rejected_nodes[:20]):
                if node.bounds is None:
                    continue
                rejected.append(
                    PreviewMatch(
                        index=index,
                        bounds=node.bounds,
                        label=(node.name or node.id or "rejected")[:48],
                        confidence=float(node.state.get("confidence") or 0.0),
                        kind="vision",
                        rejected=True,
                    )
                )
        capture_meta = self._last_capture[1] if self._last_capture else {}
        self._last_find_debug = VisionPreviewDebug(
            selector=selector,
            selected_index=selector.index,
            raw_match_count=raw_count,
            filtered_match_count=filtered_count,
            rejected=rejected,
            capture_meta=dict(capture_meta),
        )

    def _node_from_ocr(self, box: OcrTextBox, *, index: int, anchor: str, capture_meta: dict[str, Any]) -> ControlNode:
        node_id = f"vision:ocr:{index}:{anchor}"
        return ControlNode(
            id=node_id,
            backend=self.name,
            role=ControlRole.UNKNOWN,
            name=box.text,
            bounds=box.bounds,
            state={
                "ocr": True,
                "confidence": box.confidence,
                "anchor": anchor,
                "capture": capture_meta,
            },
        )

    def _node_from_template(
        self,
        match: TemplateMatch,
        *,
        index: int,
        selector: ControlSelector,
        capture_meta: dict[str, Any],
    ) -> ControlNode:
        label = selector.vision_template or selector.vision_target or f"template-{index}"
        node_id = f"vision:template:{index}:{label}"
        state: dict[str, Any] = {
            "template": True,
            "confidence": match.confidence,
            "method": match.method,
            "capture": capture_meta,
        }
        if selector.vision_anchor_rel:
            state["anchor_rel"] = selector.vision_anchor_rel
        if selector.vision_anchor:
            state["anchor"] = selector.vision_anchor
        return ControlNode(
            id=node_id,
            backend=self.name,
            role=ControlRole.UNKNOWN,
            name=label,
            bounds=match.bounds,
            state=state,
        )

    def _node_from_anchor(
        self,
        box: OcrTextBox,
        *,
        index: int,
        selector: ControlSelector,
        capture_meta: dict[str, Any],
    ) -> ControlNode:
        anchor = selector.vision_anchor or box.text
        node_id = f"vision:anchor:{index}:{anchor}"
        return ControlNode(
            id=node_id,
            backend=self.name,
            role=ControlRole.UNKNOWN,
            name=box.text,
            bounds=box.bounds,
            state={
                "anchor": True,
                "anchor_rel": selector.vision_anchor_rel,
                "anchor_label": selector.vision_anchor,
                "target": selector.vision_target,
                "confidence": box.confidence,
                "capture": capture_meta,
            },
        )

    @staticmethod
    def _selector_wants_ocr(selector: ControlSelector) -> bool:
        return bool(
            selector.text
            or selector.text_contains
            or selector.name
            or selector.name_contains
            or (selector.vision_anchor and not selector.vision_anchor_rel)
        )

    def _find_nodes(self, selector: ControlSelector) -> list[ControlNode]:
        """Priority cascade: OCR → template → anchor → stub."""
        # Fast path: pure stub anchor when OCR/template are unavailable
        if selector.vision_anchor and not selector.vision_anchor_rel and not selector.vision_template and not ocr_available()[0]:
            return self._stub_anchor_node(selector.vision_anchor)

        png: bytes | None = None
        capture_meta: dict[str, Any] = {}

        if self._selector_wants_ocr(selector) and ocr_available()[0]:
            png, capture_meta = self._capture_png()
            nodes = self._ocr_nodes_from_png(selector, png, capture_meta)
            if nodes:
                return nodes

        if selector.vision_template and template_available()[0]:
            png, capture_meta = self._ensure_png(png, capture_meta)
            nodes = self._template_nodes_from_png(selector, png, capture_meta)
            if nodes:
                return nodes

        if selector.vision_anchor_rel and selector.vision_anchor:
            png, capture_meta = self._ensure_png(png, capture_meta)
            nodes = self._anchor_nodes_from_png(selector, png, capture_meta)
            if nodes:
                return nodes

        if selector.vision_anchor and not ocr_available()[0] and not selector.vision_template:
            return self._stub_anchor_node(selector.vision_anchor)
        return []

    def _ensure_png(self, png: bytes | None, capture_meta: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
        """Return cached PNG or capture a fresh one."""
        if png is not None:
            return png, capture_meta
        return self._capture_png()

    def _template_nodes_from_png(
        self,
        selector: ControlSelector,
        png: bytes,
        capture_meta: dict[str, Any],
    ) -> list[ControlNode]:
        try:
            matches = template_find_selector(png, selector)
        except FileNotFoundError as exc:
            raise VDisplayError(str(exc)) from exc
        filtered, _picked = resolve_vision_matches(matches, selector)
        nodes: list[ControlNode] = []
        for index, item in enumerate(filtered):
            node = self._node_from_template(item, index=index, selector=selector, capture_meta=capture_meta)
            node.state.update(
                disambiguation_meta(
                    match_count=len(filtered),
                    selected_index=selector.index if selector.index < len(filtered) else None,
                    min_confidence=selector.vision_min_confidence,
                )
            )
            nodes.append(node)
        return nodes

    def _anchor_nodes_from_png(
        self,
        selector: ControlSelector,
        png: bytes,
        capture_meta: dict[str, Any],
    ) -> list[ControlNode]:
        if not ocr_available()[0]:
            return []

        combined = ocr_anchor_combined_find(
            png,
            template_path=selector.vision_template,
            anchor_text=selector.vision_anchor or "",
            relation=selector.vision_anchor_rel or "near",
            target_text=selector.vision_target or selector.text or selector.text_contains,
            anchor_index=selector.index,
            vision_min_confidence=selector.vision_min_confidence,
        )
        filtered, _picked = resolve_vision_matches(combined, selector)
        nodes: list[ControlNode] = []
        for index, item in enumerate(filtered):
            if isinstance(item, TemplateMatch):
                node = self._node_from_template(item, index=index, selector=selector, capture_meta=capture_meta)
            elif isinstance(item, OcrTextBox):
                node = self._node_from_anchor(item, index=index, selector=selector, capture_meta=capture_meta)
            else:
                continue
            node.state.update(
                disambiguation_meta(
                    match_count=len(filtered),
                    selected_index=selector.index if selector.index < len(filtered) else None,
                    min_confidence=selector.vision_min_confidence,
                )
            )
            nodes.append(node)
        return nodes

    def _ocr_nodes_from_png(
        self,
        selector: ControlSelector,
        png: bytes,
        capture_meta: dict[str, Any],
    ) -> list[ControlNode]:
        all_boxes, matched = ocr_find_selector(png, selector)
        self._last_ocr_boxes = all_boxes
        if not matched:
            self._record_find_debug(selector=selector, raw_count=0, filtered_count=0)
            return []

        filtered, _picked = resolve_vision_matches(matched, selector)
        if self._preview_debug_enabled:
            kept = {self._box_key(box) for box in filtered}
            rejected_boxes = [box for box in matched if self._box_key(box) not in kept]
            self._record_find_debug(
                selector=selector,
                raw_count=len(matched),
                filtered_count=len(filtered),
                rejected_boxes=rejected_boxes,
            )
        nodes: list[ControlNode] = []
        for index, box in enumerate(filtered):
            anchor = selector.vision_anchor or box.text
            node = self._node_from_ocr(box, index=index, anchor=anchor, capture_meta=capture_meta)
            node.state.update(
                disambiguation_meta(
                    match_count=len(filtered),
                    selected_index=selector.index if selector.index < len(filtered) else None,
                    min_confidence=selector.vision_min_confidence,
                )
            )
            nodes.append(node)
        return nodes

    def _stub_anchor_node(self, anchor: str) -> list[ControlNode]:
        node_id = f"vision:{anchor}"
        return [
            ControlNode(
                id=node_id,
                backend=self.name,
                role=ControlRole.UNKNOWN,
                name=anchor,
                bounds=ControlBounds(x=0, y=0, width=0, height=0),
                state={"stub": True, "anchor": anchor},
            )
        ]

    def snapshot(
        self,
        *,
        window_id: str | None = None,
        app: str | None = None,
        max_depth: int = 8,
    ) -> ControlSnapshot:
        snapshot = ControlSnapshot(
            backend=self.name,
            window_id=window_id,
            app_label=app,
            nodes={},
            root_ids=[],
        )
        self._cache = snapshot
        return snapshot

    def find(self, selector: ControlSelector) -> list[ControlNode]:
        snapshot = self._cache or self.snapshot()
        nodes = self._find_nodes(selector)
        if not nodes:
            if selector.vision_anchor and not ocr_available()[0] and not selector.vision_template:
                nodes = self._stub_anchor_node(selector.vision_anchor)
            else:
                if self._preview_debug_enabled:
                    self._record_find_debug(selector=selector, raw_count=0, filtered_count=0)
                return []

        if self._preview_debug_enabled and self._last_find_debug is None:
            self._record_find_debug(
                selector=selector,
                raw_count=len(nodes),
                filtered_count=len(nodes),
            )

        for node in nodes:
            snapshot.nodes[node.id] = node
        snapshot.root_ids = [node.id for node in nodes]
        self._cache = snapshot
        return nodes

    def _node_for(self, element_id: str) -> ControlNode:
        snapshot = self._cache or self.snapshot()
        node = snapshot.nodes.get(element_id)
        if node is None:
            raise VDisplayError(
                f"vision: unknown element {element_id} — call find() first or use a valid vision match id"
            )
        return node

    def _click_node(self, node: ControlNode) -> dict[str, Any]:
        if node.bounds is None:
            return {"ok": False, "element_id": node.id, "reason": "no bounds for vision target"}
        capture_meta = (node.state or {}).get("capture")
        click_point_payload = (node.state or {}).get("click_point")
        click_point = None
        if isinstance(click_point_payload, dict):
            click_point = (int(click_point_payload.get("x") or 0), int(click_point_payload.get("y") or 0))
        click = self._pointer_click_at(
            node.bounds,
            capture_meta=capture_meta,
            click_point=click_point,
        )
        return {
            **click,
            "element_id": node.id,
            "backend": self.name,
            "action": "invoke",
        }

    def invoke_map_node(self, node: ControlNode) -> dict[str, Any]:
        return self._click_node(node)

    def focus_map_node(self, node: ControlNode) -> dict[str, Any]:
        result = self._click_node(node)
        result["method"] = "focus-click"
        return result

    def set_value_map_node(self, node: ControlNode, value: str) -> dict[str, Any]:
        focus = self.focus_map_node(node)
        if not focus.get("ok"):
            return {**focus, "value": value, "action": "set_value"}
        if self._pointer_type is not None:
            self._pointer_type(value)
            return {
                "ok": True,
                "element_id": node.id,
                "value": value,
                "method": "injected-type",
                "action": "set_value",
            }
        try:
            from ....input.resolve import resolve_pointer_input

            _inp, method = resolve_pointer_input(display=self.display)
            time.sleep(0.35)
            _can_type = getattr(_inp, "can_type", None)
            if _can_type is None or _can_type():
                _inp.type_text(value)
                return {
                    "ok": True,
                    "element_id": node.id,
                    "value": value,
                    "method": f"{method}-type",
                    "action": "set_value",
                }
            _can_paste = getattr(_inp, "can_paste", None)
            if _can_paste is not None and _can_paste():
                _paste_ok, _paste_reason = self._paste_value(value, _inp)
                if _paste_ok:
                    return {
                        "ok": True,
                        "element_id": node.id,
                        "value": value,
                        "method": f"{method}-paste",
                        "action": "set_value",
                    }
                _paste_err = f"; paste fallback failed: {_paste_reason}"
            else:
                _paste_err = "; paste fallback not available (can_paste=False)"
            return {
                "ok": False,
                "element_id": node.id,
                "value": value,
                "reason": f"typing not available on this host ({method} can_type=False){_paste_err}",
                "action": "set_value",
            }
        except Exception as exc:
            return {
                "ok": False,
                "element_id": node.id,
                "value": value,
                "reason": f"type failed ({exc})",
                "action": "set_value",
            }

    def _pointer_click_at(
        self,
        bounds: ControlBounds,
        *,
        capture_meta: dict[str, Any] | None = None,
        click_point: tuple[int, int] | None = None,
    ) -> dict[str, Any]:
        if bounds.width <= 0 or bounds.height <= 0:
            return {"ok": False, "reason": "vision match has no pixel bounds — use x11/atspi fallback"}
        if click_point is not None:
            local_cx, local_cy = click_point
        else:
            click_bounds = action_bounds_for_vision(bounds)
            local_cx, local_cy = click_bounds.center
        if self._pointer_click is not None:
            self._pointer_click(local_cx, local_cy)
            return {"ok": True, "method": "injected-pointer", "x": local_cx, "y": local_cy}
        try:
            from ....input.coords import global_pointer_coords
            from ....input.resolve import resolve_pointer_input

            gx, gy, mapping = global_pointer_coords(
                local_cx,
                local_cy,
                capture_meta,
                display=self.display,
            )
            inp, method = resolve_pointer_input(display=self.display)
            inp.move(gx, gy)
            inp.click(1)
            return {
                "ok": True,
                "method": method,
                "x": gx,
                "y": gy,
                "local_x": local_cx,
                "local_y": local_cy,
                "coord_mapping": mapping,
            }
        except Exception as exc:
            return {
                "ok": False,
                "reason": f"pointer click failed ({exc}) — route via x11/atspi/uia/ax fallback",
                "x": local_cx,
                "y": local_cy,
            }

    def invoke(self, element_id: str, *, action: str | None = None) -> dict[str, Any]:
        node = self._node_for(element_id)
        if node.bounds is None:
            return {"ok": False, "stub": True, "element_id": element_id, "reason": "no bounds for vision target"}
        capture_meta = (node.state or {}).get("capture")
        click_point_payload = (node.state or {}).get("click_point")
        click_point = None
        if isinstance(click_point_payload, dict):
            click_point = (int(click_point_payload.get("x") or 0), int(click_point_payload.get("y") or 0))
        click = self._pointer_click_at(
            node.bounds,
            capture_meta=capture_meta,
            click_point=click_point,
        )
        payload = {
            "backend": self.name,
            "element_id": element_id,
            "action": action,
            **click,
        }
        if node.state.get("stub"):
            payload["stub"] = True
            payload["ok"] = False
            payload["reason"] = "vision stub anchor without OCR/template bounds"
        return payload

    def focus(self, element_id: str) -> dict[str, Any]:
        result = self.invoke(element_id, action="focus")
        result["method"] = "focus-click"
        return result

    def set_value(self, element_id: str, value: str) -> dict[str, Any]:
        node = self._node_for(element_id)
        if node.bounds is None or node.bounds.width <= 0:
            return {"ok": False, "element_id": element_id, "reason": "no vision bounds for set_value"}
        focus = self.focus(element_id)
        if not focus.get("ok"):
            return {**focus, "value": value}
        if self._pointer_type is not None:
            self._pointer_type(value)
            return {"ok": True, "element_id": element_id, "value": value, "method": "injected-type"}
        try:
            from ....input.resolve import resolve_pointer_input

            _inp, method = resolve_pointer_input(display=self.display)
            time.sleep(0.35)
            _can_type = getattr(_inp, "can_type", None)
            if _can_type is None or _can_type():
                _inp.type_text(value)
                return {"ok": True, "element_id": element_id, "value": value, "method": f"{method}-type"}
            # Fallback: paste via clipboard + hotkey if the backend supports it
            _can_paste = getattr(_inp, "can_paste", None)
            if _can_paste is not None and _can_paste():
                _paste_ok, _paste_reason = self._paste_value(value, _inp)
                if _paste_ok:
                    return {
                        "ok": True,
                        "element_id": element_id,
                        "value": value,
                        "method": f"{method}-paste",
                    }
                _paste_err = f"; paste fallback failed: {_paste_reason}"
            else:
                _paste_err = "; paste fallback not available (can_paste=False)"
            return {
                "ok": False,
                "element_id": element_id,
                "value": value,
                "reason": f"typing not available on this host ({method} can_type=False){_paste_err}",
            }
        except Exception as exc:
            return {
                "ok": False,
                "element_id": element_id,
                "value": value,
                "reason": f"type failed ({exc})",
            }

    def _paste_value(self, value: str, _inp) -> tuple[bool, str]:
        """Copy value to clipboard and send Ctrl+V via the input backend."""
        import shutil
        import subprocess
        import time

        # Prefer wl-copy on Wayland, xclip on X11
        if shutil.which("wl-copy"):
            try:
                subprocess.run(["wl-copy"], input=value.encode(), check=True, timeout=5)
            except Exception as exc:
                return False, f"wl-copy failed: {exc}"
        elif shutil.which("xclip"):
            try:
                subprocess.run(
                    ["xclip", "-selection", "clipboard"],
                    input=value.encode(),
                    check=True,
                    timeout=5,
                )
            except Exception as exc:
                return False, f"xclip failed: {exc}"
        else:
            return False, "no clipboard utility (wl-copy or xclip)"
        try:
            try:
                _inp.hotkey("ctrl", "a")
            except TypeError:
                _inp.hotkey("ctrl+a")
            time.sleep(0.08)
            try:
                _inp.hotkey("ctrl", "v")
            except TypeError:
                _inp.hotkey("ctrl+v")
            return True, "pasted"
        except Exception as exc:
            return False, f"paste hotkey failed: {exc}"

    def bounds(self, element_id: str) -> ControlBounds | None:
        node = self._node_for(element_id)
        return node.bounds


VisionProviderStub = VisionStubProvider
