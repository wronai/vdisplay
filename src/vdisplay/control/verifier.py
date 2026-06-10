"""Unified verify-after-action pipeline: semantic, visual, OCR."""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from typing import Any, Callable

from .base import ControlProvider
from .contracts import VerifySpec
from .gui_map import GuiMapElement, verify_hints_from_map_element
from .models import ControlNode, ControlSnapshot
from .screenshot_verify import (
    _region_from_bounds,
    capture_control_screenshot,
    verify_screenshot_pair,
)
from .selector import ControlSelector
from .verify import verify_action_result

CaptureFn = Callable[..., bytes]


@dataclass(frozen=True)
class VerifyContext:
    action_provider: ControlProvider
    before_snapshot: ControlSnapshot
    target: ControlNode
    action: str
    selector: ControlSelector
    session_id: str | None = None
    value: str | None = None
    verify_label: str | None = None
    verify_selector: str | None = None
    display: str | None = None
    capture_fn: CaptureFn | None = None
    before_png: bytes | None = None
    before_capture_meta: dict[str, Any] | None = None
    verify_semantic: bool = False
    verify_screenshot: bool = False
    verify_mode: str = "semantic"
    verify_provider: str | None = None
    spec: VerifySpec | None = None
    map_element: GuiMapElement | None = None


@dataclass
class VerificationResult:
    verified: bool | None
    mode: str
    confidence: float = 0.0
    semantic: dict[str, Any] | None = None
    visual: dict[str, Any] | None = None
    ocr: dict[str, Any] | None = None
    vision_llm: dict[str, Any] | None = None
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verified": self.verified,
            "mode": self.mode,
            "confidence": self.confidence,
            "semantic": self.semantic,
            "visual": self.visual,
            "ocr": self.ocr,
            "vision_llm": self.vision_llm,
            "reasons": list(self.reasons),
        }


def verify_spec_from_flags(
    *,
    verify_semantic: bool,
    verify_screenshot: bool,
    verify_mode: str,
    verify_label: str | None = None,
    expected_text: str | None = None,
) -> VerifySpec | None:
    if not verify_semantic and not verify_screenshot:
        return None
    if verify_semantic and verify_screenshot:
        mode = "hybrid"
    elif verify_screenshot:
        mode = "screenshot_diff"
    elif verify_mode in {
        "semantic",
        "hybrid",
        "dom",
        "anchor_visible",
        "ocr_contains",
        "screenshot_diff",
        "identity+region",
    }:
        mode = "ocr_contains" if verify_mode == "identity+region" else verify_mode
    else:
        mode = "semantic"
    min_change_ratio = 0.00005 if verify_screenshot else 0.02
    return VerifySpec(
        mode=mode,  # type: ignore[arg-type]
        expected_text=expected_text or verify_label,
        min_change_ratio=min_change_ratio,
    )


def _region_for_verify(ctx: VerifyContext, spec: VerifySpec) -> tuple[int, int, int, int] | None:
    region = spec.region
    if region is None and ctx.map_element is not None:
        bounds = ctx.map_element.action_bounds.to_control_bounds()
        if bounds.width > 0 and bounds.height > 0:
            region = _region_from_bounds(bounds)
    if (
        region is None
        and ctx.action == "set_value"
        and ctx.target is not None
        and ctx.target.bounds is not None
        and ctx.target.bounds.width > 0
    ):
        from .action_bounds import action_bounds_for_vision

        bounds = action_bounds_for_vision(ctx.target.bounds)
        region = _region_from_bounds(bounds, padding=4)
    return region


def _ocr_text_contains(expected: str, text: str) -> bool:
    if expected and len(expected) > 24 and "-" in expected:
        tokens = [part for part in expected.replace("_", "-").split("-") if len(part) >= 3]
        if tokens:
            return all(token.lower() in text.lower() for token in tokens)
    return expected.lower() in text.lower()


def _vision_rescue_result(
    *,
    spec: VerifySpec,
    verified: bool,
    confidence: float,
    reason: str,
    vision_llm_payload: dict[str, Any] | None,
    visual: dict[str, Any] | None = None,
    ocr: dict[str, Any] | None = None,
) -> VerificationResult:
    return VerificationResult(
        verified=verified,
        mode=spec.mode,
        confidence=confidence,
        visual=visual,
        ocr=ocr,
        vision_llm=vision_llm_payload,
        reasons=[reason],
    )


class VerifierPipeline:
    def _run_semantic_if_needed(
        self,
        ctx: VerifyContext,
    ) -> tuple[dict[str, Any] | None, bool | None]:
        if not ctx.verify_semantic:
            return None, None
        semantic_payload = self._run_semantic(ctx)
        return semantic_payload, bool(semantic_payload.get("verified"))

    def _run_visual_if_needed(
        self,
        ctx: VerifyContext,
        spec: VerifySpec,
        semantic_ok: bool | None,
    ) -> tuple[dict[str, Any] | None, bool | None]:
        need_visual = ctx.verify_screenshot or (
            spec.mode == "hybrid"
            and ctx.verify_semantic
            and not ctx.verify_screenshot
            and semantic_ok is False
        )
        if need_visual and ctx.before_png is not None:
            visual_payload = self._run_visual(ctx, spec)
            return visual_payload, bool(visual_payload.get("verified"))
        if ctx.verify_screenshot and ctx.before_png is None:
            return {"verified": False, "reason": "missing before screenshot"}, False
        return None, None

    def _maybe_ocr_rescue(
        self,
        ctx: VerifyContext,
        spec: VerifySpec,
        visual_payload: dict[str, Any] | None,
        visual_ok: bool | None,
    ) -> tuple[dict[str, Any] | None, bool | None, dict[str, Any] | None]:
        if not (
            spec.expected_text
            and visual_payload
            and visual_ok is False
            and spec.mode in {"hybrid", "ocr_contains"}
        ):
            return visual_payload, visual_ok, None
        ocr_payload = self._run_ocr(ctx, spec, visual_payload)
        if ocr_payload and ocr_payload.get("verified"):
            return {**visual_payload, "ocr_rescue": ocr_payload}, True, ocr_payload
        return visual_payload, visual_ok, ocr_payload

    def _evaluate_runs(
        self,
        ctx: VerifyContext,
        spec: VerifySpec,
    ) -> tuple[dict[str, Any] | None, bool | None, dict[str, Any] | None, bool | None, dict[str, Any] | None]:
        semantic_payload, semantic_ok = self._run_semantic_if_needed(ctx)
        visual_payload, visual_ok = self._run_visual_if_needed(ctx, spec, semantic_ok)
        visual_payload, visual_ok, ocr_payload = self._maybe_ocr_rescue(ctx, spec, visual_payload, visual_ok)
        return semantic_payload, semantic_ok, visual_payload, visual_ok, ocr_payload

    def verify_after_action(self, ctx: VerifyContext) -> VerificationResult:
        spec = ctx.spec or verify_spec_from_flags(
            verify_semantic=ctx.verify_semantic,
            verify_screenshot=ctx.verify_screenshot,
            verify_mode=ctx.verify_mode,
            verify_label=ctx.verify_label,
            expected_text=ctx.value,
        )
        if spec is None:
            return VerificationResult(verified=None, mode="none", confidence=0.0)

        if spec.mode == "anchor_visible":
            return self._verify_anchor_visible(ctx, spec)
        if spec.mode == "ocr_contains":
            return self._verify_ocr_contains(ctx, spec)
        return self._verify_combined(ctx, spec)

    def _verify_anchor_visible(self, ctx: VerifyContext, spec: VerifySpec) -> VerificationResult:
        anchor_payload = self._run_anchor_visible(ctx, spec)
        label = spec.expected_text or ctx.selector.vision_anchor or ctx.verify_label
        return self._verify_with_vision_rescue(
            ctx,
            spec,
            primary_payload=anchor_payload,
            primary_verified=bool(anchor_payload.get("verified")),
            payload_key="visual",
            expected_text=label,
            anchor_label=label,
            ok_reason="anchor visible",
            fail_reason="anchor not visible",
        )

    def _verify_ocr_contains(self, ctx: VerifyContext, spec: VerifySpec) -> VerificationResult:
        ocr_payload = self._run_ocr(ctx, spec, {})
        return self._verify_with_vision_rescue(
            ctx,
            spec,
            primary_payload=ocr_payload or {},
            primary_verified=bool(ocr_payload and ocr_payload.get("verified")),
            payload_key="ocr",
            expected_text=spec.expected_text,
            ok_reason="ocr text matched",
            fail_reason="ocr text missing",
        )

    def _verify_with_vision_rescue(
        self,
        ctx: VerifyContext,
        spec: VerifySpec,
        *,
        primary_payload: dict[str, Any],
        primary_verified: bool,
        payload_key: str,
        expected_text: str | None = None,
        anchor_label: str | None = None,
        ok_reason: str,
        fail_reason: str,
    ) -> VerificationResult:
        verified = primary_verified
        vision_llm_payload = None
        if not verified:
            vision_llm_payload = self._maybe_vision_llm_fallback(
                ctx,
                spec,
                expected_text=expected_text,
                anchor_label=anchor_label,
            )
            if vision_llm_payload and vision_llm_payload.get("verified"):
                verified = True
        confidence = float(
            (vision_llm_payload or {}).get("confidence")
            or primary_payload.get("confidence")
            or (0.9 if verified else 0.0)
        )
        reason = str(
            (vision_llm_payload or {}).get("reason")
            or primary_payload.get("reason")
            or (ok_reason if verified else fail_reason)
        )
        kwargs: dict[str, Any] = {
            "spec": spec,
            "verified": verified,
            "confidence": confidence,
            "reason": reason,
            "vision_llm_payload": vision_llm_payload,
        }
        if payload_key == "visual":
            kwargs["visual"] = primary_payload
        else:
            kwargs["ocr"] = primary_payload
        return _vision_rescue_result(**kwargs)

    def _verify_combined(self, ctx: VerifyContext, spec: VerifySpec) -> VerificationResult:
        semantic_payload, semantic_ok, visual_payload, visual_ok, ocr_payload = self._evaluate_runs(ctx, spec)

        verified, confidence, reasons = self._aggregate(
            spec=spec,
            verify_semantic=ctx.verify_semantic,
            verify_screenshot=ctx.verify_screenshot,
            semantic_ok=semantic_ok,
            visual_ok=visual_ok,
            semantic_payload=semantic_payload,
            visual_payload=visual_payload,
        )
        return VerificationResult(
            verified=verified,
            mode=spec.mode,
            confidence=confidence,
            semantic=semantic_payload,
            visual=visual_payload,
            ocr=ocr_payload,
            reasons=reasons,
        )

    def _run_semantic(self, ctx: VerifyContext) -> dict[str, Any]:
        after_snapshot = ctx.action_provider.snapshot(
            app=ctx.selector.app or ctx.session_id,
            window_id=ctx.selector.window_id or ctx.session_id,
        )
        verify_label = ctx.verify_label
        verify_selector = ctx.verify_selector
        if ctx.map_element is not None:
            hints = verify_hints_from_map_element(ctx.map_element)
            verify_label = verify_label or hints.get("verify_label")
            verify_selector = verify_selector or hints.get("verify_selector")
        payload = verify_action_result(
            before=ctx.before_snapshot,
            after=after_snapshot,
            target=ctx.target,
            action=ctx.action,
            expected_value=ctx.value,
            verify_label=verify_label,
            verify_selector=verify_selector,
        )
        payload["provider"] = getattr(ctx.action_provider, "name", "unknown")
        if ctx.verify_mode == "dom" or (ctx.spec and ctx.spec.mode == "dom"):
            payload["verify_kind"] = "dom"
        if ctx.verify_provider and ctx.verify_provider != payload["provider"]:
            payload["verify_provider"] = ctx.verify_provider
        return payload

    def _run_visual(self, ctx: VerifyContext, spec: VerifySpec) -> dict[str, Any]:
        after_png, after_meta = capture_control_screenshot(
            display=ctx.display,
            target=ctx.target,
            capture_fn=ctx.capture_fn,
        )
        compare_region = _region_for_verify(ctx, spec)
        if compare_region is None and ctx.target.bounds is not None:
            if ctx.target.bounds.width > 0 and ctx.target.bounds.height > 0:
                compare_region = _region_from_bounds(ctx.target.bounds)
        result = verify_screenshot_pair(
            ctx.before_png or b"",
            after_png,
            region=compare_region,
            min_changed_ratio=spec.min_change_ratio,
        )
        result["capture"] = {
            "before": ctx.before_capture_meta,
            "after": after_meta,
        }
        result["provider"] = ctx.verify_provider or getattr(ctx.action_provider, "name", "unknown")
        return result

    def _run_ocr(
        self,
        ctx: VerifyContext,
        spec: VerifySpec,
        visual_payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        after_capture = (visual_payload.get("capture") or {}).get("after")
        if after_capture is None and ctx.before_png is None and spec.mode != "ocr_contains":
            return None
        from .vision_ocr import ocr_available, ocr_png

        ready, reason = ocr_available()
        if not ready:
            return {"verified": False, "reason": reason, "method": "ocr"}

        after_png = after_capture
        if after_png is None:
            after_png, after_meta = capture_control_screenshot(
                display=ctx.display,
                target=ctx.target,
                capture_fn=ctx.capture_fn,
            )
        else:
            after_meta = (visual_payload.get("capture") or {}).get("after_meta") or {}

        sidecar_path = (
            (ctx.before_capture_meta or {}).get("screen_context_path")
            or after_meta.get("screen_context_path")
            or (visual_payload.get("screen_context") or {}).get("path")
        )
        if sidecar_path:
            import os

            os.environ.setdefault("VDISPLAY_SCREEN_CONTEXT_PATH", str(sidecar_path))
        region = _region_for_verify(ctx, spec)
        if region is not None:
            from PIL import Image

            image = Image.open(io.BytesIO(after_png))
            x, y, w, h = region
            buf = io.BytesIO()
            image.crop((x, y, x + w, y + h)).save(buf, format="PNG")
            after_png = buf.getvalue()

        boxes = ocr_png(after_png)
        text = " ".join(box.text for box in boxes)
        expected = spec.expected_text or ""
        found = _ocr_text_contains(expected, text)
        confidence = 0.9 if found else 0.0
        return {
            "verified": found and confidence >= spec.min_confidence,
            "method": "ocr",
            "expected_text": expected,
            "text": text.strip(),
            "confidence": confidence,
            "boxes": [box.to_dict() for box in boxes[:20]],
        }

    def _maybe_vision_llm_fallback(
        self,
        ctx: VerifyContext,
        spec: VerifySpec,
        *,
        expected_text: str | None = None,
        anchor_label: str | None = None,
    ) -> dict[str, Any] | None:
        from .vision_llm import verify_text_in_region, vision_llm_fallback_enabled

        if not vision_llm_fallback_enabled():
            return None

        after_png, _after_meta = capture_control_screenshot(
            display=ctx.display,
            target=ctx.target,
            capture_fn=ctx.capture_fn,
        )
        region = spec.region
        if region is None and ctx.map_element is not None:
            bounds = ctx.map_element.action_bounds.to_control_bounds()
            if bounds.width > 0 and bounds.height > 0:
                region = _region_from_bounds(bounds)

        return verify_text_in_region(
            after_png,
            expected_text or "",
            region=region,
            anchor_label=anchor_label,
        )

    def _run_anchor_visible(self, ctx: VerifyContext, spec: VerifySpec) -> dict[str, Any]:
        """PR-22 — confirm template PNG or OCR anchor label is still visible after action."""
        after_png, after_meta = capture_control_screenshot(
            display=ctx.display,
            target=ctx.target,
            capture_fn=ctx.capture_fn,
        )

        if ctx.selector.vision_template:
            from .vision_template import template_available, template_find_selector

            ready, reason = template_available()
            if not ready:
                return {"verified": False, "method": "template", "reason": reason, "capture": after_meta}
            matches = template_find_selector(
                after_png,
                ctx.selector,
                threshold=spec.min_confidence,
            )
            found = bool(matches)
            return {
                "verified": found,
                "method": "template",
                "confidence": float(matches[0].confidence) if matches else 0.0,
                "match_count": len(matches),
                "capture": after_meta,
            }

        anchor_label = spec.expected_text or ctx.selector.vision_anchor or ctx.verify_label
        if not anchor_label:
            return {
                "verified": False,
                "method": "anchor_visible",
                "reason": "missing vision_template or vision_anchor/expected_text for anchor_visible verify",
                "capture": after_meta,
            }

        from .vision_ocr import ocr_available, ocr_png, match_selector_boxes

        ready, reason = ocr_available()
        if not ready:
            return {"verified": False, "method": "ocr_anchor", "reason": reason, "capture": after_meta}

        boxes = ocr_png(after_png)
        matched = match_selector_boxes(boxes, ControlSelector(vision_anchor=anchor_label))
        found = bool(matched)
        confidence = float(matched[0].confidence) if matched else 0.0
        return {
            "verified": found and confidence >= spec.min_confidence,
            "method": "ocr_anchor",
            "expected_text": anchor_label,
            "confidence": confidence,
            "match_count": len(matched),
            "capture": after_meta,
        }

    def _aggregate(
        self,
        *,
        spec: VerifySpec,
        verify_semantic: bool,
        verify_screenshot: bool,
        semantic_ok: bool | None,
        visual_ok: bool | None,
        semantic_payload: dict[str, Any] | None,
        visual_payload: dict[str, Any] | None,
    ) -> tuple[bool | None, float, list[str]]:
        if verify_semantic and verify_screenshot:
            return _aggregate_dual(semantic_ok, visual_ok)

        if verify_screenshot and not verify_semantic:
            return _aggregate_screenshot_only(visual_ok)

        if verify_semantic and not verify_screenshot:
            return _aggregate_semantic_only(spec.mode, semantic_ok, visual_ok)

        return None, 0.0, []


def _aggregate_dual(semantic_ok: bool | None, visual_ok: bool | None) -> tuple[bool, float, list[str]]:
    reasons = []
    verified = bool(semantic_ok) and bool(visual_ok)
    confidence = 0.95 if verified else 0.0
    if semantic_ok is False:
        reasons.append("semantic verify failed")
    if visual_ok is False:
        reasons.append("visual verify failed")
    if verified:
        reasons.append("strict dual verify passed")
    return verified, confidence, reasons


def _aggregate_screenshot_only(visual_ok: bool | None) -> tuple[bool, float, list[str]]:
    verified = bool(visual_ok)
    return verified, 0.85 if verified else 0.0, ["screenshot verify only"]


def _aggregate_semantic_only(
    spec_mode: str,
    semantic_ok: bool | None,
    visual_ok: bool | None,
) -> tuple[bool, float, list[str]]:
    reasons = []
    if semantic_ok:
        return True, 0.9, ["semantic verify passed"]
    if spec_mode == "hybrid" and visual_ok:
        return True, 0.75, ["semantic failed; visual verify rescued action"]
    if semantic_ok is False:
        reasons.append("semantic verify failed")
    return False, 0.0, reasons


_default_pipeline = VerifierPipeline()


def default_verifier() -> VerifierPipeline:
    return _default_pipeline
