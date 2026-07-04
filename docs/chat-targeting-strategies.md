# Chat-input targeting strategies

How vdisplay decides **where to click** to drop a prompt into an IDE's AI
chat composer, which strategies exist, the order they are tried, and which
one to prefer for a given environment.

This concerns the *targeting* problem only — "which pixel is the chat input".
The separate *actuation* problem ("synthesize the click + keystrokes") is
covered in [`control-plane.md`](control-plane.md) and the OS-injector docs.

---

## TL;DR — the decision the library makes

```
detect_chat_click_target(png, ide=...)        # vdisplay.control.vision_chat_detect
│
├─ 1. OCR placeholder anchor      ── deterministic, no LLM, cheapest, most precise
│      ocr_anchor_chat_target()      when the placeholder text is on screen
│
├─ 2. Crop cascade (in turns)     ── small LLM payloads, high precision
│      right_half → q_tr → q_br      one region per LLM call, first hit wins
│      → q_bl → q_tl                 (VDISPLAY_VISION_CROP_PASSES)
│
└─ 3. Full-image LLM query        ── last resort; imprecise on dense screenshots
       (single detect + one re-probe)
```

Upstream of all three, koru's photo-VQL pipeline first tries **OCR/VQL layer
analysis** (`imgl_resolve_chat_target`) and only falls to vision detection
when those layers are empty, polluted, or disagree with the expected IDE.
So the full stack is: **VQL layers → OCR anchor → crop cascade → full-image LLM**.

---

## The strategies, in order

### 0. VQL / OCR layer analysis (koru side, `imgl_resolve_chat_target`)

- **What**: builds a semantic layer map of the screenshot (windows, labels,
  inputs) and picks the best chat-input candidate from it.
- **Cost**: one OCR pass, no LLM.
- **Best when**: the capture is clean and the chat input is a well-formed,
  reasonably-sized element that OCR/layout resolves unambiguously.
- **Fails when**: multi-panel monitors produce degraded/tiny elements or
  terminal-noise labels; the picked element is a small OCR fragment, not the
  real composer. When its candidate looks suspicious, control passes to vision.

### 1. OCR placeholder anchor — `ocr_anchor_chat_target()`

- **What**: run tesseract, find the input's **placeholder text** by token
  (`autonomously` for Qoder's "Plan and build autonomously", `anything` for
  Cursor/Windsurf's "Ask anything", `copilot` for VS Code), and click the
  **center of that word's bounding box**. The placeholder sits *inside* the
  empty input, so its bbox center is inside the input.
- **Cost**: one OCR pass, **zero LLM calls**, deterministic.
- **Precision**: exact (pixel bbox from tesseract).
- **Best when**: the chat panel is open and *empty* (placeholder visible), on
  any monitor layout. This is the **preferred** strategy — try it first.
- **Fails when**: the input already has user text (placeholder gone), the
  placeholder is a custom string not in `_CHAT_PLACEHOLDER_TOKENS`, or OCR
  can't read it (low contrast/scaling). Then fall through.
- **Guardrails**: token *priority* beats OCR reading order (a distinctive
  placeholder token wins over a brand token that also appears elsewhere), and
  brand tokens in the top 15 % strip (panel title bar) are skipped so the
  anchor never lands on the "Qoder"/"Copilot" heading instead of the input.
- **Extending**: add your IDE's placeholder token to
  `_CHAT_PLACEHOLDER_TOKENS[<ide>]`. Prefer a word that appears *only* in the
  input placeholder, never in the title bar or menus.

### 2. Crop cascade — small regions to the LLM, in turns

- **What**: when no OCR anchor, query the vision LLM on **cropped regions**
  instead of the full screenshot, one region per call, adding the crop's
  `(dx, dy)` offset back to the returned coords. Order (clockwise from
  top-right, chat panels dock right):
  `right_half → q_tr → q_br → q_bl → q_tl`. First accepted hit wins
  (early-exit), so a right-docked chat is usually found on pass 1–2.
- **Cost**: 1–N LLM calls, but each payload is 2–8× smaller than the full
  frame, so total tokens are typically *lower* than one full-image call, and
  precision is much higher.
- **Precision**: high — a vision LLM localizes accurately on a small,
  low-clutter crop even when it can't on the dense full frame.
- **Best when**: the placeholder isn't OCR-readable but the panel is visible,
  and you know roughly which region it's in (right/quadrant).
- **Config**: `VDISPLAY_VISION_CROP_PASSES` (comma list; reorder or shorten to
  match your layout; `off`/`none` disables the cascade).
- **Why not just crop around the model's own guess?** Measured: the model's
  full-frame guesses are *systematically* off (clustered ~800 px from truth),
  not noisy — a crop around a wrong guess wouldn't contain the target.
  Hypothesis-driven region crops (where panels actually dock) do contain it.

### 3. Full-image LLM query — last resort

- **What**: send the whole screenshot and ask for the chat-input coords;
  `detect_chat_click_target` does one primary query, and
  `probe_chat_click_target`/`resolve_chat_target_from_screenshot` adds a
  second-pass query if the first returns nothing.
- **Cost**: 1–2 large LLM calls.
- **Precision**: **poor on dense multi-panel screenshots** — the model
  identifies the input correctly by description ("the Qoder input") but returns
  coords ~800 px off. Adequate on simple/single-panel layouts.
- **Best when**: nothing else applies and the layout is simple.

---

## Acceptance guards (applied to every LLM-sourced target)

`llm_decision_rejects_chat_target()` filters vision coords before they are
trusted. A target is rejected when:

- the LLM's *reason* says it couldn't find a trustworthy target
  (`_REJECT_REASON_MARKERS`);
- the reason **names a competing IDE** — matched as **whole words**;
  `cursor` counts only with an app qualifier ("Cursor IDE/editor", "in
  Cursor"), never for the benign "text/mouse cursor" the model mentions when
  describing an input field;
- the coords are the bottom-right-corner fallback (≥97 % w and h);
- for JetBrains, `y` is above the chat zone — `< VDISPLAY_JB_CHAT_MIN_Y_FRAC`
  (default **0.25**; the old hard-coded 0.55 wrongly rejected right-docked
  panels whose input sits mid-height).

The OCR anchor bypasses these coordinate guards (its coords come from a real
bbox, not model inference) but still carries `llm_decision.confidence = 0.95`
so downstream verification treats it as a confirmed target.

---

## How koru consumes a located target (verification gates)

Once a target is located, koru's drive path checks it against several gates.
The governing principle: **when vision located the target, VQL-layer
heuristics do not veto it** (the vision layer has its own confidence +
geometry guards). Concretely, under
`KORU_VDISPLAY_LLM_VISION_DECISION=1`:

| Gate | Assumes | Deferred to vision because |
|------|---------|----------------------------|
| capture-title match | window title says "PyCharm" | a right-docked panel's monitor OCRs as the editor breadcrumb |
| VQL structure_ok | well-formed VQL layers | vision reads the raw PNG, not the layers |
| map-source match | GUI map monitor == capture | vision needs no stored map |
| command-plan bounds | composer is a large bottom-right element | a placeholder bbox is small but exact |
| coord sanity (y≥850, x≥1100) | chat is bottom-right | Qoder/AI-Assistant dock right, input mid-height |

A **competing-IDE** capture (a Cursor/VSCode window on the target monitor) is
never deferred — that always blocks, vision or not.

---

## Choosing per environment

| Environment / layout | Prefer | Why |
|----------------------|--------|-----|
| Chat panel open + empty (placeholder visible) | **OCR anchor** | deterministic, no LLM, exact, layout-independent |
| Right-docked chat (Qoder, AI Assistant), busy multi-panel | OCR anchor → **right_half crop** | full-frame LLM is imprecise here; cropping fixes it |
| Input already has text (no placeholder) | crop cascade | anchor can't fire; small crops keep precision |
| Simple/single-panel IDE | full-image LLM is fine | little clutter, model localizes well |
| Native-Wayland IDE, no window titles | vision path + surface registry | title-match can't confirm; vision + surface do |
| X11 with a calibrated GUI map | VQL/map path | deterministic map coords, no vision needed |
| No OpenRouter key | **OCR anchor only** (+ VQL/map) | vision LLM disabled; anchor still works |

Rule of thumb: **more panels / more clutter on screen ⇒ prefer OCR anchor,
then crops; reserve the full-image LLM for simple layouts.** The single
biggest precision win is shrinking what the model sees.

---

## Environment variables

| Var | Effect | Default |
|-----|--------|---------|
| `VDISPLAY_VISION_CHAT_DETECT` | enable vision chat detection (needs `OPENROUTER_API_KEY`) | off |
| `KORU_VDISPLAY_LLM_VISION_DECISION` | let a vision-located target override VQL-layer gates | off |
| `VDISPLAY_VISION_CROP_PASSES` | crop cascade order; `off` disables | `right_half,q_tr,q_br,q_bl,q_tl` |
| `VDISPLAY_JB_CHAT_MIN_Y_FRAC` | min y-fraction a JetBrains chat target may sit at | `0.25` |
| `VDISPLAY_VISION_LLM` | vision model id | `openrouter/google/gemini-3.1-flash-image-preview` |

---

## Coordinate-validation monitoring layer

Targeting says *which capture pixel* to hit; **actuation** must then move the OS
pointer there, and the capture→global mapping (`global_pointer_coords`)
compounds unknowns — capture-vs-region scale, ydotool absolute-axis semantics,
HiDPI, monitor offsets. When any is off the pointer lands on the wrong spot (or
the wrong monitor). `vdisplay.capture.coordinate_validation` **measures** the
mapping instead of trusting it (numpy-only; `opencv` optional for higher-accuracy
matching):

- **`locate_cursor_in_frame(png, template=…)`** — single-frame detection: find
  the cursor (or any element) on ONE static screenshot via masked normalized
  cross-correlation (`match_template`). Use when vdisplay only has an image to
  identify a position on — no pointer movement. Verified on a real 2560×1600
  capture (exact hit, score 1.0).
- **`locate_cursor(source, at_global, …)`** — move-and-diff detection robust to
  live content (terminals/animations): park the cursor off-source, capture, move
  it to the probe, capture twice, and take the pixelwise **minimum of two
  difference frames** — only the consistently-present cursor survives; a
  box-sum peak picks the compact bright blob over diffuse background churn.
- **`which_monitor_has_cursor(at_global, sources, …)`** — after a move, report
  which monitor's capture shows the cursor: the safety check that the pointer is
  on the IDE's screen, not a neighbour, before typing.
- **`validate_pointer_mapping(target_local, meta, source, …)`** — move to the
  computed global and measure the capture-space error; feeds the monitor.
- **`converge_pointer_to_local(target_local, …)`** — closed-loop adaptive
  positioning: nudge by `gain`×observed-error (converted to units via an
  empirical `probe_pointer_scale`) until within tolerance. Precision through
  adaptation, independent of every absolute-mapping unknown.
- **`CoordinateValidationMonitor`** — append-only JSONL + summary (success rate,
  mean/max error, off-monitor count, per-source) so mapping drift or a coord
  regression surfaces as a rising error rate, not a silent mis-click.

Prefer the closed loop on multi-monitor / HiDPI where the absolute mapping is
unreliable; the single-frame detector when you only have a still screenshot.

## Assessing which strategy fired / why one fails

`probe_chat_click_target()` returns full diagnostics — the raw LLM text,
parsed coords, confidence, and the rejection verdict. The tell-tale for a
**model precision** problem (vs a capture or pipeline problem) is a **correct
description with wrong coords**: the reason names the right element ("the
Qoder input placeholder") while the coords are far from it. That signature
means *shrink the image* (anchor or crop) rather than retrying the full frame
— retrying returns the same systematically-wrong coordinates.

Log lines to grep:
- `vision_chat_detect ocr_anchor …` — anchor fired (best case)
- `vision_chat_detect crop_hit pass=… …` — a crop pass won
- `vision_chat_detect rejected … reason=…` — a guard rejected an LLM target
- `VQL_CHAT_WRITE_BLOCKED_SUSPICIOUS_COORDS …` (koru) — coord-sanity block
  (should not fire for a vision-located target under the vision opt-in)
