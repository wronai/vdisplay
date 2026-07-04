# Pointer positioning on Wayland — problem, decisions, solutions

How vdisplay moves the OS pointer to an exact capture pixel (e.g. an IDE chat
input) on GNOME Wayland, why the obvious approach fails, and the layered
solution in `vdisplay.capture.coordinate_validation`.

This is the **actuation** half of driving a chat panel; the **targeting** half
(which pixel to hit) is in [chat-targeting-strategies.md](chat-targeting-strategies.md).

---

## The problem

Targeting gives a capture-pixel `(lx, ly)` for the chat input. To click it we
must move the OS pointer to the matching **global** desktop coordinate and
click. The map capture-pixel → global is where everything went wrong: the
pointer kept landing far off — in one case on a different monitor entirely.

---

## Why you can't just read the pointer position

The natural fix — "move, read where the cursor actually is, correct" — needs to
**read** the pointer position. On Wayland that is essentially unavailable:

- **Wayland** deliberately hides the global pointer position from clients (no
  `XQueryPointer` equivalent) — a security/isolation decision.
- **evdev** (`/dev/input/event*`): an ordinary mouse emits **relative** motion
  (`REL_X/REL_Y`) only; there is no absolute readout. Only absolute devices
  (tablets/touchscreens, `ABS_X/ABS_Y`) expose position, and a mouse isn't one.
- **GNOME** knows the position (`global.get_pointer()`) but Shell **Eval /
  Introspect is locked** on current GNOME, so we can't ask it.

Conclusion: **reading is out; we must positively CONTROL and MEASURE.**

---

## What the mapping actually depends on (the compounding unknowns)

`global_pointer_coords()` computes global from capture-local using:

1. **capture-vs-region scale** — the capture PNG (e.g. 2560×1600) is smaller
   than the monitor region it represents (e.g. 4096×2560); the scale factor
   (≈1.6) must be applied. Missing PNG dimensions in the meta silently defaulted
   the scale to **1.0**, so a right-side target landed ~1.6× too far left.
2. **ydotool absolute-axis semantics** — how the injected coordinate maps to
   pixels. Opaque and version-dependent.
3. **HiDPI logical-vs-physical** — the compositor's logical space may be scaled
   down from the physical resolution.
4. **monitor offsets** — DP-1 at `(0, 658)`, DP-2 at `(4096, 0)`, etc. An x
   error of one scale factor pushes the pointer onto the neighbour monitor.

Each is an estimate; the errors multiply. Applying a "correct-looking" scale of
1.6 overshot onto another monitor — proof that at least one other factor
(ydotool's axis) was also off. **Predicting the mapping from first principles is
unreliable.**

---

## Empirical findings (measured, not assumed)

- **The screencast embeds the cursor.** The portal is opened with
  `VDISPLAY_SCREENCAST_CURSOR=2` (EMBEDDED), so a screenshot *shows* the cursor
  — we can see where it landed even though we can't query it.
- **ydotool here is ABSOLUTE.** This build has no `--absolute` flag and
  `mousemove x y` moves *to* a coordinate: issuing the same `mousemove 600 400`
  twice left the cursor at the same capture pixel `(1499, 993)`. So the
  wrong-monitor jump was a **scale** error, not relative accumulation.
- **The vision LLM localizes poorly on dense frames** (separate finding): it
  describes the input correctly but returns pixel coords ~800px off — which is
  why targeting shrinks the image (OCR anchor / crop). Same lesson here:
  measure, don't predict.

---

## The solution, layer by layer (and why each decision)

### 1. See the cursor — robustly and cheaply

- **Single-frame** (`locate_cursor_in_frame` / `match_template`): find the
  cursor (or any element) on ONE static screenshot via masked normalized
  cross-correlation. For when only an image is available.
- **Move-and-diff** (`locate_cursor`): park the cursor off-source, capture,
  move to the probe, capture twice; the **pixelwise minimum of two difference
  frames** keeps only the consistently-present cursor. A **box-sum peak** picks
  the compact bright blob, rejecting large diffuse changes.
  - *Decision:* a naive full-frame diff locked onto a live terminal (measured
    1143 false blobs). The min-of-two + box-sum fixes it.

### 2. Analyse one quadrant at a time — never the whole frame

`find_cursor_by_quadrant(expected_quadrant=…)` and `_single_diff_peak(region=…)`
split the frame into quadrants and analyse the **most-probable one first** (where
the cursor was just commanded), then the rest in dock-order.

- *Decision:* full-frame numpy analysis is slow (2560×1600) AND fragile — a live
  region in another quadrant hijacks the peak. Per-quadrant is ~4× cheaper and a
  terminal in a *different* quadrant is simply never looked at.

### 3. Calibrate the mapping ONCE — don't loop every click

`calibrate_pointer_affine()` measures the true ydotool→capture mapping with a
few captures, fits an axis-aligned affine `local = a·global + b`, and caches it.
All subsequent clicks convert target→global **open-loop, zero captures**.

- *Decision:* a per-click closed loop did 3 screenshots × N iterations at ~6s
  each — 5+ minutes. Since ydotool is absolute, the mapping is *stable*: measure
  it once, reuse forever. Re-calibrate only on a layout change.

### 4. Avoid live quadrants + fit robustly

`detect_live_quadrants()` (two captures, no move) flags quadrants that change on
their own; calibration **skips probes** whose quadrant is live and fits with one
round of **residual outlier rejection**.

- *Decision:* on the real monitor the terminal quadrant ate 2 of 4 probes and
  collapsed the fit to zero slope (`ax=0`). Avoiding that quadrant + a denser
  grid + outlier drop restored a real slope (`ax≈0.72`).

### 5. Corner anchor — the "known zero"

`park_at_corner()` slams the pointer far beyond a screen edge; the compositor
**clamps** it to that corner — a guaranteed, UI-independent reference we *can*
establish even though we can't read the position. Calibration records it and
**validates the fit**: the cursor must land in the expected corner's quadrant,
and the distance to the exact corner is a quality signal (`residual_px`).

- *Decision:* reading position is blocked, but *establishing* a known one by
  clamping is not. A corner is unambiguous (no UI sits exactly there), so the
  detector locks on cleanly, giving a reliable anchor and a cheap sanity check
  that the whole calibration is oriented correctly. (The clamp command is
  saturated, so it anchors/validates but is not a linear fit point.)

### 6. Closed-loop adaptive positioning — the fallback

`converge_pointer_to_local()` nudges by `gain × observed-error` (converted to
units via `probe_pointer_scale`) until within tolerance — precision through
adaptation, for when a cached affine isn't trusted. Slower (captures per
iteration); use when calibration is stale or unavailable.

### 7. Monitor the mapping over time

`validate_pointer_mapping()` + `CoordinateValidationMonitor` measure the
capture-space error of a mapping and record it (append-only JSONL + summary:
success rate, mean/max error, off-monitor count). Drift or a regression in the
coordinate math shows up as a rising error rate, not a silent mis-click.

---

## Alternatives considered

- **Own uinput ABSOLUTE device.** Create a virtual pointer via `/dev/uinput`
  with `ABS_X/ABS_Y` over a fixed range mapped to the screen — then *we* own the
  mapping and absolute positioning is fully deterministic (what tablets do).
  Cleanest long-term, but requires device setup and permissions; deferred
  because ydotool is already absolute and the affine calibration removes its
  opacity. **This is the recommended next step if ydotool's mapping ever proves
  unstable.**
- **Corner-clamp + pure relative motion.** If the injector were relative, park
  at a corner (known origin) and issue pixel deltas. Not needed here — ydotool
  is absolute — but the corner-anchor above reuses the same "known zero" idea.
- **Low-level position reading.** Blocked on Wayland (see above); not viable.

---

## Choosing per situation

| Situation | Use |
|-----------|-----|
| Repeated clicks, stable layout | `calibrate_pointer_affine` once → cached affine, open-loop |
| One static screenshot, no control of the pointer | `locate_cursor_in_frame` (single-frame) |
| Live content (terminal) on the monitor | quadrant-scoped detection + `avoid_live_quadrants` |
| Calibration stale / untrusted | `converge_pointer_to_local` (closed loop) |
| Need a guaranteed reference | `park_at_corner` (known zero) |
| Want to track mapping health | `CoordinateValidationMonitor` |

**Rule of thumb:** measure the mapping once against reality and cache it; never
predict it from first principles, and never analyse the whole frame when one
quadrant will do.

---

## koru integration

Under `KORU_VDISPLAY_ADAPTIVE_POINTER=1`, koru's actuation path confirms the
pointer is on the IDE's monitor (`which_monitor_has_cursor`) and runs the
closed loop before typing, falling back to the open-loop mapping otherwise.
Default (flag off) behaviour is unchanged.

## Environment variables

| Var | Effect | Default |
|-----|--------|---------|
| `VDISPLAY_SCREENCAST_CURSOR` | portal cursor mode (2 = embedded, needed to see the cursor) | 2 |
| `KORU_VDISPLAY_ADAPTIVE_POINTER` | koru: use the closed loop before typing | off |
