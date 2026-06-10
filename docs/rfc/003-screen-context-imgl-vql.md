# RFC-003: ScreenContext + IMGL + VQL integration

> **Status:** Etap 1–2 implemented (vdisplay shims + IMGL `vision_ops`); Etap 3 partial (`img2vql.vdisplay_context`)  
> **Goal:** vdisplay exports reusable screen metadata; IMGL owns pixels; VQL owns scene IR and reverse generation.

## Problem

vdisplay mixes capture orchestration with OCR/template/preview logic. IMGL and VQL already implement scene analysis and metadata programs, but there is no stable contract between them and vdisplay session/control flows.

## Architecture

| Layer | Repo | Responsibility |
|-------|------|----------------|
| Context | **vdisplay** | Capture, windows, maps, routing, verify, `ScreenContext` |
| Pixels | **IMGL** | OCR, scene layout, annotated previews, scene cache |
| IR | **VQL** | `VQLProgram`, metadata validation, SVG/layout render, reverse descriptors |

## ScreenContext (vdisplay)

Module: `src/vdisplay/integrations/screen_context.py`

```text
ScreenContext
  capture      # display, monitor, region, method, path
  environment  # platform, monitors, windows, routing, map
  vision       # preview, actuation, local OCR/template (legacy)
  map_pack     # GUI map JSON when --map attached
  verify       # verify phases from control diagnostics
  imgl         # IMGL scene analysis result
  vql          # VQL program + reverse descriptor
  artifacts    # paths: context, vql, svg, map
  nl           # human summary
  fingerprint  # sha256 prefix for cache keys
```

Sidecar: `screen.png.context.json` next to each observed screenshot.

## Pipeline

```text
capture/screenshot
  → screen_context_from_capture()
  → [optional] imgl.analyze / scene_cache
  → [optional] vql program merge (metadata.capture, environment, gui_map)
  → [optional] render_to_svg
  → write sidecar + session artifacts
```

Env:

| Variable | Default | Meaning |
|----------|---------|---------|
| `VDISPLAY_OBSERVE` | on when IMGL/VQL enabled | Run observe enrichment after screenshot |
| `VDISPLAY_IMGL` | `1` | Call IMGL analyze |
| `VDISPLAY_VQL` | `1` | Export VQL JSON (+ SVG when `--svg`) |
| `VDISPLAY_VISION_BACKEND` | `auto` | `local` \| `imgl` \| `auto` for OCR/template/diff/preview delegation |

## CLI

```bash
vdisplay observe -o screen.png --map maps/chat.json --vql layout.vql.json --svg layout.svg
vdisplay observe --format summary
export VDISPLAY_OBSERVE=1
vdisplay --session screenshot -o step.png   # auto sidecar when IMGL/VQL installed
```

## Migration plan (cross-repo)

### Etap 1 — vdisplay contract ✅

- `ScreenContext`, `observe` command, `enrich_capture_payload` hook
- Optional extras: `vdisplay[observe]`, `[imgl]`, `[vql]`

### Etap 2 — IMGL owns image ops ✅ (shims)

Move from vdisplay → IMGL (via adapter, keep shims):

- `vision_ocr.py` → `imgl.ocr` (+ selector find in IMGL or thin vdisplay wrapper)
- `vision_template.py` → `imgl.vision_ops.match_template_png`
- `vision_preview.py` → `imgl.vision_ops.render_match_overlay_png`
- `screenshot_verify.py` diff primitives → `imgl.vision_ops.diff_png_bytes`
- `img2nl_enrich.py` → delegate describe path to IMGL/VQL metadata ✅ (`VDISPLAY_DESCRIBE_BACKEND`)

vdisplay keeps: `VisionStubProvider` routing, map resolve, verify policy.

### Etap 3 — VQL metadata-first (partial ✅)

Extend VQL / img2vql:

- `from_screen_context(ctx)` importer ✅
- `reverse_generate(program)` → layout.svg + prompt_block ✅
- Validated blocks: `metadata.capture`, `metadata.environment`, `metadata.gui_map`, `metadata.render_intent` (partial)

### Etap 4 — incremental analysis cache ✅ (core)

- Reuse `ScreenContext.fingerprint` + GUI map drift gate (`evaluate_map_drift`, `map_drift_blocks_cache`)
- Session store: `artifacts/observe/<fingerprint>.context.json`, `artifacts/vql/<fingerprint>.vql.json`
- Control verify: `screen_context_path` on capture meta → cached OCR via sidecar

## Reverse image generation levels

1. **Layout** — VQL program → `render_to_svg` (UI, maps)
2. **Semantic** — `metadata.render_intent.prompt_block` → external generative model
3. **Hybrid** — IMGL region crops + VQL scene graph + refine

Implemented in vdisplay: `reverse_generation_descriptor()` builds level-1/2 hints from `ScreenContext`.

## Related

- [session-report.md](../guides/session-report.md) — audit artifacts
- IMGL: `imgl/vdisplay_bridge.py` (inverse direction today)
- VQL: `docs/vdisplay-imgl-automation.md`, `validate_program_metadata`
