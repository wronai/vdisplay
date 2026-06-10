"""Vision-only surface provider — OCR, template, and spatial anchor find/invoke (PR-20/22)."""

from __future__ import annotations

import os
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
            return self._capture_fn(display=self.display)
        return capture_control_screenshot(display=self.display, target=target, capture_fn=None)

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
        if selector.vision_anchor and not selector.vision_anchor_rel and not selector.vision_template:
            if not ocr_available()[0]:
                return self._stub_anchor_node(selector.vision_anchor)

        png: bytes | None = None
        capture_meta: dict[str, Any] = {}

        if self._selector_wants_ocr(selector) and ocr_available()[0]:
            png, capture_meta = self._capture_png()
            nodes = self._ocr_nodes_from_png(selector, png, capture_meta)
            if nodes:
                return nodes

        if selector.vision_template and template_available()[0]:
            if png is None:
                png, capture_meta = self._capture_png()
            nodes = self._template_nodes_from_png(selector, png, capture_meta)
            if nodes:
                return nodes

        if selector.vision_anchor_rel and selector.vision_anchor:
            if png is None:
                png, capture_meta = self._capture_png()
            nodes = self._anchor_nodes_from_png(selector, png, capture_meta)
            if nodes:
                return nodes

        if selector.vision_anchor and not ocr_available()[0] and not selector.vision_template:
            return self._stub_anchor_node(selector.vision_anchor)
        return []

    def _template_nodes_from_png(
        self,
        selector: ControlSelector,
        png: bytes,
        capture_meta: dict[str, Any],
    ) -> list[ControlNode]:
        matches = template_find_selector(png, selector)
        return [
            self._node_from_template(item, index=index, selector=selector, capture_meta=capture_meta)
            for index, item in enumerate(matches)
        ]

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
        )
        nodes: list[ControlNode] = []
        for index, item in enumerate(combined):
            if isinstance(item, TemplateMatch):
                nodes.append(
                    self._node_from_template(item, index=index, selector=selector, capture_meta=capture_meta)
                )
            elif isinstance(item, OcrTextBox):
                nodes.append(self._node_from_anchor(item, index=index, selector=selector, capture_meta=capture_meta))
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
            return []

        nodes: list[ControlNode] = []
        for index, box in enumerate(matched):
            anchor = selector.vision_anchor or box.text
            nodes.append(self._node_from_ocr(box, index=index, anchor=anchor, capture_meta=capture_meta))
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
                return []

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

    def _pointer_click_at(self, bounds: ControlBounds) -> dict[str, Any]:
        if bounds.width <= 0 or bounds.height <= 0:
            return {"ok": False, "reason": "vision match has no pixel bounds — use x11/atspi fallback"}
        cx, cy = bounds.center
        if self._pointer_click is not None:
            self._pointer_click(cx, cy)
            return {"ok": True, "method": "injected-pointer", "x": cx, "y": cy}
        try:
            from ....discovery import resolve_host_display
            from ....input.linux_xdotool import LinuxXdotoolInput

            display = resolve_host_display(self.display or os.environ.get("DISPLAY"))
            inp = LinuxXdotoolInput(display)
            inp.move(cx, cy)
            inp.click(1)
            return {"ok": True, "method": "xdotool", "x": cx, "y": cy}
        except Exception as exc:
            return {
                "ok": False,
                "reason": f"pointer click failed ({exc}) — route via x11/atspi/uia/ax fallback",
                "x": cx,
                "y": cy,
            }

    def invoke(self, element_id: str, *, action: str | None = None) -> dict[str, Any]:
        node = self._node_for(element_id)
        if node.bounds is None:
            return {"ok": False, "stub": True, "element_id": element_id, "reason": "no bounds for vision target"}
        click = self._pointer_click_at(node.bounds)
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
            from ....discovery import resolve_host_display
            from ....input.linux_xdotool import LinuxXdotoolInput

            display = resolve_host_display(self.display or os.environ.get("DISPLAY"))
            LinuxXdotoolInput(display).type_text(value)
            return {"ok": True, "element_id": element_id, "value": value, "method": "xdotool-type"}
        except Exception as exc:
            return {
                "ok": False,
                "element_id": element_id,
                "value": value,
                "reason": f"type failed ({exc})",
            }

    def bounds(self, element_id: str) -> ControlBounds | None:
        node = self._node_for(element_id)
        return node.bounds


VisionProviderStub = VisionStubProvider
