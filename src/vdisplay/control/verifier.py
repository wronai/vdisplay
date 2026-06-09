"""Unified verify-after-action pipeline: semantic, visual, OCR."""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from typing import Any, Callable

from .base import ControlProvider
from .contracts import VerifySpec
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


@dataclass
class VerificationResult:
    verified: bool | None
    mode: str
    confidence: float = 0.0
    semantic: dict[str, Any] | None = None
    visual: dict[str, Any] | None = None
    ocr: dict[str, Any] | None = None
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verified": self.verified,
            "mode": self.mode,
            "confidence": self.confidence,
            "semantic": self.semantic,
            "visual": self.visual,
            "ocr": self.ocr,
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
    else:
        mode = verify_mode if verify_mode in {"semantic", "hybrid", "dom"} else "semantic"
    min_change_ratio = 0.00005 if verify_screenshot else 0.02
    return VerifySpec(
        mode=mode,  # type: ignore[arg-type]
        expected_text=expected_text or verify_label,
        min_change_ratio=min_change_ratio,
    )


class VerifierPipeline:
    def _evaluate_runs(
        self,
        ctx: VerifyContext,
        spec: VerifySpec,
    ) -> tuple[dict[str, Any] | None, bool | None, dict[str, Any] | None, bool | None, dict[str, Any] | None]:
        semantic_payload: dict[str, Any] | None = None
        semantic_ok: bool | None = None
        if ctx.verify_semantic:
            semantic_payload = self._run_semantic(ctx)
            semantic_ok = bool(semantic_payload.get("verified"))

        visual_payload: dict[str, Any] | None = None
        visual_ok: bool | None = None
        need_visual = ctx.verify_screenshot or (
            spec.mode == "hybrid"
            and ctx.verify_semantic
            and not ctx.verify_screenshot
            and semantic_ok is False
        )
        if need_visual and ctx.before_png is not None:
            visual_payload = self._run_visual(ctx, spec)
            visual_ok = bool(visual_payload.get("verified"))
        elif ctx.verify_screenshot and ctx.before_png is None:
            visual_payload = {"verified": False, "reason": "missing before screenshot"}
            visual_ok = False

        ocr_payload: dict[str, Any] | None = None
        if (
            spec.expected_text
            and visual_payload
            and visual_ok is False
            and spec.mode in {"hybrid", "ocr_contains"}
        ):
            ocr_payload = self._run_ocr(ctx, spec, visual_payload)
            if ocr_payload and ocr_payload.get("verified"):
                visual_ok = True
                visual_payload = {**visual_payload, "ocr_rescue": ocr_payload}

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
        payload = verify_action_result(
            before=ctx.before_snapshot,
            after=after_snapshot,
            target=ctx.target,
            action=ctx.action,
            expected_value=ctx.value,
            verify_label=ctx.verify_label,
            verify_selector=ctx.verify_selector,
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
        compare_region = spec.region
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
        if after_capture is None and ctx.before_png is None:
            return None
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            return {"verified": False, "reason": "pytesseract not installed", "method": "ocr"}

        after_png, _meta = capture_control_screenshot(
            display=ctx.display,
            target=ctx.target,
            capture_fn=ctx.capture_fn,
        )
        image = Image.open(io.BytesIO(after_png))
        if spec.region is not None:
            x, y, w, h = spec.region
            image = image.crop((x, y, x + w, y + h))
        text = pytesseract.image_to_string(image)
        expected = spec.expected_text or ""
        found = expected.lower() in text.lower()
        confidence = 0.9 if found else 0.0
        return {
            "verified": found and confidence >= spec.min_confidence,
            "method": "ocr",
            "expected_text": expected,
            "text": text.strip(),
            "confidence": confidence,
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
