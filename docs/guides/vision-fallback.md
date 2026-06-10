# Guide: vision verify and LLM fallback

**Question:** How does OCR verify work, and when does the cold-path vision LLM run?

## Verify tiers (hot / warm / cold)

| Tier | Component | Role |
|------|-----------|------|
| Hot | Tesseract OCR + map bounds | Find targets, `ocr_contains` verify |
| Warm | `VerifierPipeline`, map diff | Post-action verify, drift detection |
| Cold | `VDISPLAY_VISION_LLM_*` | Fallback when OCR verify fails; optional enrich |

Cold path is **separate from** orchestration `LLM_MODEL` — do not mix them.

## Enable vision LLM (cold path)

```bash
LLM_MODEL=openrouter/qwen/qwen3-coder-next          # orchestration (unchanged)

VDISPLAY_VISION_LLM=openrouter/google/gemini-3.1-flash-image-preview
VDISPLAY_VISION_LLM_ENABLED=1
VDISPLAY_VISION_LLM_MODE=fallback    # off | fallback | enrich | both
OPENROUTER_API_KEY=sk-or-v1-...
```

All vision LLM env vars: [reference/env.md](../reference/env.md)

## Verify modes (after control action)

| Mode | Use when |
|------|----------|
| `ocr_contains` | Expect typed text in field (set-value) |
| `anchor_visible` | Label/placeholder still visible = fail |
| `screenshot_diff` | Visual change in region |
| `identity+region` | Map default → resolves to OCR or anchor |

CLI: `--verify`, `--screenshot-verify`, `--verify-label`, `--verify-selector`

## set-value hard verify (recommended)

For vision/ydotool backends, treat success only when:

1. **Negative:** placeholder text (`Ask`, `anything`) gone from input crop.
2. **Positive:** expected value or prefix visible in crop.

If paste was sent but placeholder remains → `ok: false`, `reason: text_not_applied`.

## img2nl enrichment (optional)

`VDISPLAY_IMG2NL=1` adds NL metadata to VQL programs — not required for control hot path.

Details: [vision-only-wayland.md](../vision-only-wayland.md) · Control plane: [control-plane.md](../control-plane.md)
