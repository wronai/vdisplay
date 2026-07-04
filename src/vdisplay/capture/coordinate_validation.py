"""Coordinate-validation monitoring layer.

The absolute capture→pointer mapping (``global_pointer_coords``) compounds
several unknowns — capture-vs-region scale, ydotool absolute-axis semantics,
HiDPI logical-vs-physical scaling, monitor offsets. Any one being off sends the
pointer to the wrong place (measured: onto the wrong monitor entirely).

This layer replaces *trusting* the mapping with *measuring* it. Because the
portal screencast embeds the cursor (``VDISPLAY_SCREENCAST_CURSOR=2``), we can
move the pointer, screenshot, and SEE where it actually landed — then:

  * ``validate_pointer_mapping`` — check a computed mapping against reality and
    record the error (monitoring);
  * ``locate_cursor`` — find the cursor pixel robustly even over live content
    (terminals, animations) via presence-consistency differencing;
  * ``converge_pointer_to_local`` — closed-loop adaptive positioning: nudge the
    pointer, re-observe, correct by a fraction until within tolerance — precision
    through adaptation, independent of every mapping unknown;
  * ``CoordinateValidationMonitor`` — append-only record + summary of mapping
    accuracy over time (drift/regressions surface here).

numpy-only (no OpenCV): the cursor detector uses the pixelwise minimum of two
independent difference frames, which suppresses uncorrelated background churn.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol

# A function that moves the OS pointer to an absolute global (x, y).
MoveFn = Callable[[int, int], None]
# A function that returns a fresh PNG (bytes) for the given source/monitor.
CaptureFn = Callable[[str], bytes]


class _Clock(Protocol):
    def __call__(self) -> float: ...


def _png_to_gray(png: bytes) -> tuple["Any", int, int]:
    """Decode a PNG to a 2-D uint8 grayscale numpy array (h, w)."""
    import io

    import numpy as np
    from PIL import Image

    with Image.open(io.BytesIO(png)) as img:
        arr = np.asarray(img.convert("L"), dtype=np.int16)
    h, w = arr.shape[:2]
    return arr, w, h


@dataclass(frozen=True)
class CursorLocation:
    """A detected cursor position in capture-pixel space."""

    x: int
    y: int
    confidence: float
    source: str
    method: str = "diff"

    def to_dict(self) -> dict[str, Any]:
        return {
            "x": self.x,
            "y": self.y,
            "confidence": round(self.confidence, 4),
            "source": self.source,
            "method": self.method,
        }


def _default_cursor_template() -> "Any":
    """A synthetic left-tip arrow cursor (white fill, dark border) as a small
    grayscale template. Good enough for NCC against most themed arrow cursors;
    pass a real cursor crop for maximum accuracy."""
    import numpy as np

    h, w = 22, 16
    tpl = np.full((h, w), -1.0)  # -1 = "don't care" (transparent)
    for y in range(h):
        span = int(w * (1 - y / h))
        if span <= 0:
            continue
        for x in range(min(span, w)):
            # border on the diagonal / left edge, white fill inside
            tpl[y, x] = 30.0 if (x == 0 or x == span - 1 or y == h - 1) else 235.0
    return tpl


def match_template(
    haystack_png: bytes,
    template: "Any",
    *,
    threshold: float = 0.5,
    search_region: tuple[int, int, int, int] | None = None,
) -> tuple[int, int, float] | None:
    """Locate ``template`` in a single screenshot via masked normalized
    cross-correlation (numpy only). Returns (center_x, center_y, score) of the
    best match, or None below ``threshold``.

    ``template`` is a 2-D float array; cells < 0 are treated as transparent
    ("don't care"), so an arrow cursor's non-rectangular shape matches cleanly.
    ``search_region`` = (x0, y0, x1, y1) restricts the search (e.g. the expected
    monitor / panel) for speed and to reject far-off false peaks.
    """
    import numpy as np

    img, iw, ih = _png_to_gray(haystack_png)
    img = img.astype(np.float64)
    th, tw = template.shape
    if ih < th or iw < tw:
        return None
    x0, y0, x1, y1 = search_region or (0, 0, iw, ih)
    x0 = max(0, min(x0, iw - tw))
    y0 = max(0, min(y0, ih - th))
    x1 = max(x0 + 1, min(x1, iw - tw + 1))
    y1 = max(y0 + 1, min(y1, ih - th + 1))

    mask = template >= 0
    tvals = template[mask]
    t_mean = tvals.mean()
    t_centered = np.where(mask, template - t_mean, 0.0)
    t_norm = float(np.sqrt((t_centered[mask] ** 2).sum())) or 1.0

    best = (-1.0, 0, 0)
    for yy in range(y0, y1):
        for xx in range(x0, x1):
            patch = img[yy:yy + th, xx:xx + tw]
            pvals = patch[mask]
            p_centered = np.where(mask, patch - pvals.mean(), 0.0)
            p_norm = float(np.sqrt((p_centered[mask] ** 2).sum())) or 1.0
            score = float((t_centered * p_centered).sum() / (t_norm * p_norm))
            if score > best[0]:
                best = (score, xx, yy)
    if best[0] < threshold:
        return None
    return best[1] + tw // 2, best[2] + th // 2, best[0]


def locate_cursor_in_frame(
    png: bytes,
    source: str = "",
    *,
    template: "Any" | None = None,
    threshold: float = 0.5,
    search_region: tuple[int, int, int, int] | None = None,
) -> CursorLocation | None:
    """Single-frame cursor detection for a STATIC screenshot (no pointer move).

    Used when vdisplay only has one captured image to identify the cursor
    position on — the still-image counterpart to the move-and-diff
    ``locate_cursor``. Template-matches the arrow shape.
    """
    tpl = template if template is not None else _default_cursor_template()
    hit = match_template(png, tpl, threshold=threshold, search_region=search_region)
    if hit is None:
        return None
    x, y, score = hit
    return CursorLocation(x=x, y=y, confidence=score, source=source, method="template")


def _peak_of_min_diff(base_png: bytes, on_a_png: bytes, on_b_png: bytes, *, thr: int = 40):
    """Return (x, y, score) of the cursor via presence-consistency.

    ``base`` has the cursor parked OFF this source; ``on_a`` and ``on_b`` both
    have the cursor at the SAME probe spot. |on_a-base| and |on_b-base| both
    light up the cursor position; their pixelwise MINIMUM stays bright only
    where BOTH agree — i.e. the cursor — while uncorrelated background churn (a
    blinking caret in one frame but not the other) is suppressed to near zero.

    The park position must be off-capture so ``base`` carries no cursor of its
    own; otherwise the parked cursor lights up too and skews the centroid.
    """
    import numpy as np

    base, w, h = _png_to_gray(base_png)
    a, _, _ = _png_to_gray(on_a_png)
    b, _, _ = _png_to_gray(on_b_png)
    if a.shape != base.shape or b.shape != base.shape:
        return None
    da = np.abs(a - base)
    db = np.abs(b - base)
    consistent = np.minimum(da, db).astype(np.float64)
    consistent[consistent < thr] = 0.0
    if not consistent.any():
        return None
    # Find the most cursor-DENSE window, not the global centroid: a large diffuse
    # region (a live terminal band that happens to differ in both frames) has
    # high total intensity but low local density; the compact bright cursor wins
    # a local box-sum. Integral image -> O(1) window sums.
    win = 12
    integ = consistent.cumsum(axis=0).cumsum(axis=1)
    integ = np.pad(integ, ((1, 0), (1, 0)))
    h2, w2 = consistent.shape
    box = (
        integ[win:, win:]
        - integ[:-win, win:]
        - integ[win:, :-win]
        + integ[:-win, :-win]
    )
    if box.size == 0:
        return None
    py, px_ = np.unravel_index(int(np.argmax(box)), box.shape)
    # centroid within the winning window (sub-window precision)
    y0, x0 = int(py), int(px_)
    sub = consistent[y0:y0 + win, x0:x0 + win]
    sy, sx = np.nonzero(sub)
    if sy.size == 0:
        return None
    wts = sub[sy, sx]
    cx = x0 + float((sx * wts).sum() / wts.sum())
    cy = y0 + float((sy * wts).sum() / wts.sum())
    peak_density = float(box.max()) / (win * win)
    confidence = max(0.0, min(1.0, peak_density / 255.0))
    return int(round(cx)), int(round(cy)), confidence


def locate_cursor(
    source: str,
    at_global: tuple[int, int],
    *,
    move: MoveFn,
    capture: CaptureFn,
    park_global: tuple[int, int] = (32000, 32000),
    settle: Callable[[], None] | None = None,
) -> CursorLocation | None:
    """Move the pointer to ``at_global`` and return where it actually landed in
    ``source``'s capture pixels — robust to live screen content.

    Returns None if the cursor isn't visible on this source (it went to another
    monitor, or the source didn't render it).
    """
    def _settle() -> None:
        if settle is not None:
            settle()

    move(*at_global)
    _settle()
    on_a = capture(source)
    move(*park_global)
    _settle()
    base = capture(source)
    move(*at_global)
    _settle()
    on_b = capture(source)
    found = _peak_of_min_diff(base, on_a, on_b)
    if found is None:
        return None
    x, y, conf = found
    return CursorLocation(x=x, y=y, confidence=conf, source=source)


def which_monitor_has_cursor(
    at_global: tuple[int, int],
    sources: list[str],
    *,
    move: MoveFn,
    capture: CaptureFn,
    park_global: tuple[int, int] = (32000, 32000),
    settle: Callable[[], None] | None = None,
    min_confidence: float = 0.05,
) -> tuple[str | None, CursorLocation | None]:
    """After moving to ``at_global``, report which source's capture shows the
    cursor. The safety check before typing: confirm the pointer is on the
    monitor that hosts the IDE, not a neighbour."""
    best: CursorLocation | None = None
    for src in sources:
        loc = locate_cursor(src, at_global, move=move, capture=capture, park_global=park_global, settle=settle)
        if loc is not None and loc.confidence >= min_confidence:
            if best is None or loc.confidence > best.confidence:
                best = loc
    return (best.source if best else None), best


@dataclass(frozen=True)
class MappingValidation:
    """One measured check of a computed coordinate mapping."""

    source: str
    target_local: tuple[int, int]
    expected_global: tuple[int, int]
    observed_local: tuple[int, int] | None
    error_px: float | None
    on_expected_monitor: bool
    confidence: float
    ok: bool
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target_local": list(self.target_local),
            "expected_global": list(self.expected_global),
            "observed_local": list(self.observed_local) if self.observed_local else None,
            "error_px": round(self.error_px, 1) if self.error_px is not None else None,
            "on_expected_monitor": self.on_expected_monitor,
            "confidence": round(self.confidence, 4),
            "ok": self.ok,
            "note": self.note,
        }


def validate_pointer_mapping(
    target_local: tuple[int, int],
    capture_meta: dict[str, Any],
    source: str,
    *,
    move: MoveFn,
    capture: CaptureFn,
    tolerance_px: float = 20.0,
    settle: Callable[[], None] | None = None,
) -> MappingValidation:
    """Compute the global for ``target_local``, move there, and measure how far
    the cursor actually is from ``target_local`` in capture space."""
    from .coordinate_map import global_pointer_coords

    gx, gy, _details = global_pointer_coords(int(target_local[0]), int(target_local[1]), capture_meta)
    loc = locate_cursor(source, (gx, gy), move=move, capture=capture, settle=settle)
    if loc is None:
        return MappingValidation(
            source=source,
            target_local=target_local,
            expected_global=(gx, gy),
            observed_local=None,
            error_px=None,
            on_expected_monitor=False,
            confidence=0.0,
            ok=False,
            note="cursor not visible on this source (likely landed on another monitor)",
        )
    err = math.hypot(loc.x - target_local[0], loc.y - target_local[1])
    return MappingValidation(
        source=source,
        target_local=target_local,
        expected_global=(gx, gy),
        observed_local=(loc.x, loc.y),
        error_px=err,
        on_expected_monitor=True,
        confidence=loc.confidence,
        ok=err <= tolerance_px,
        note="within tolerance" if err <= tolerance_px else "mapping error exceeds tolerance",
    )


@dataclass
class PointerScale:
    """Empirically measured ydotool-units per capture-pixel for a source."""

    units_per_px_x: float
    units_per_px_y: float
    source: str
    ok: bool

    def delta_units(self, dx_px: float, dy_px: float) -> tuple[int, int]:
        return int(round(dx_px * self.units_per_px_x)), int(round(dy_px * self.units_per_px_y))


def probe_pointer_scale(
    source: str,
    *,
    move: MoveFn,
    capture: CaptureFn,
    anchor_global: tuple[int, int] = (1200, 1200),
    step_units: int = 300,
    settle: Callable[[], None] | None = None,
) -> PointerScale:
    """Move the pointer by a known unit step twice and observe the capture-pixel
    shift, solving units/pixel — the conversion the adaptive loop needs WITHOUT
    trusting the region math."""
    p0 = locate_cursor(source, anchor_global, move=move, capture=capture, settle=settle)
    px = locate_cursor(source, (anchor_global[0] + step_units, anchor_global[1]), move=move, capture=capture, settle=settle)
    py = locate_cursor(source, (anchor_global[0], anchor_global[1] + step_units), move=move, capture=capture, settle=settle)
    if not (p0 and px and py):
        return PointerScale(1.0, 1.0, source, ok=False)
    dpx = abs(px.x - p0.x) or 1
    dpy = abs(py.y - p0.y) or 1
    return PointerScale(
        units_per_px_x=step_units / dpx,
        units_per_px_y=step_units / dpy,
        source=source,
        ok=True,
    )


@dataclass
class ConvergenceResult:
    ok: bool
    iterations: int
    final_local: tuple[int, int] | None
    final_error_px: float | None
    landed_global: tuple[int, int] | None
    trace: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "iterations": self.iterations,
            "final_local": list(self.final_local) if self.final_local else None,
            "final_error_px": round(self.final_error_px, 1) if self.final_error_px is not None else None,
            "landed_global": list(self.landed_global) if self.landed_global else None,
            "trace": self.trace,
        }


def converge_pointer_to_local(
    target_local: tuple[int, int],
    capture_meta: dict[str, Any],
    source: str,
    *,
    move: MoveFn,
    capture: CaptureFn,
    tolerance_px: float = 15.0,
    gain: float = 0.6,
    max_iters: int = 6,
    scale: PointerScale | None = None,
    settle: Callable[[], None] | None = None,
) -> ConvergenceResult:
    """Closed-loop adaptive positioning (the relative-correction approach).

    Start from the absolute best-guess global, then repeatedly observe the
    cursor, measure the capture-space error to ``target_local``, and nudge the
    pointer by ``gain`` × error (converted to units via the empirical scale)
    until within ``tolerance_px``. Robust to every absolute-mapping unknown.
    """
    from .coordinate_map import global_pointer_coords

    if scale is None:
        scale = probe_pointer_scale(source, move=move, capture=capture, settle=settle)
    gx, gy, _ = global_pointer_coords(int(target_local[0]), int(target_local[1]), capture_meta)
    trace: list[dict[str, Any]] = []
    best_err: float | None = None
    best_local: tuple[int, int] | None = None
    for i in range(max_iters):
        loc = locate_cursor(source, (gx, gy), move=move, capture=capture, settle=settle)
        if loc is None:
            trace.append({"iter": i, "global": [gx, gy], "observed": None, "note": "cursor off-source"})
            break
        err_x = target_local[0] - loc.x
        err_y = target_local[1] - loc.y
        err = math.hypot(err_x, err_y)
        trace.append({"iter": i, "global": [gx, gy], "observed": [loc.x, loc.y], "error_px": round(err, 1)})
        if best_err is None or err < best_err:
            best_err, best_local = err, (loc.x, loc.y)
        if err <= tolerance_px:
            return ConvergenceResult(True, i + 1, (loc.x, loc.y), err, (gx, gy), trace)
        du, dv = scale.delta_units(err_x * gain, err_y * gain)
        gx, gy = gx + du, gy + dv
    return ConvergenceResult(False, len(trace), best_local, best_err, (gx, gy), trace)


# Quadrants of a frame, clockwise from top-right (chat panels dock right), as
# fractional boxes (x0, y0, x1, y1). Analysing ONE quadrant is ~4x cheaper than
# the whole frame AND isolates cursor detection from churn (a live terminal) in
# a DIFFERENT quadrant — the single biggest robustness+speed win.
_QUADRANTS: dict[str, tuple[float, float, float, float]] = {
    "tr": (0.5, 0.0, 1.0, 0.5),
    "br": (0.5, 0.5, 1.0, 1.0),
    "bl": (0.0, 0.5, 0.5, 1.0),
    "tl": (0.0, 0.0, 0.5, 0.5),
}
# Order to try, most-probable first: right-docked chat panels live on the right.
_QUADRANT_ORDER = ("tr", "br", "bl", "tl")


def quadrant_of_local(x: int, y: int, w: int, h: int) -> str:
    """Which quadrant capture pixel (x, y) falls in."""
    right = x >= w * 0.5
    bottom = y >= h * 0.5
    if right and not bottom:
        return "tr"
    if right and bottom:
        return "br"
    if not right and bottom:
        return "bl"
    return "tl"


def _quadrant_box_px(quadrant: str, w: int, h: int) -> tuple[int, int, int, int]:
    fx0, fy0, fx1, fy1 = _QUADRANTS[quadrant]
    return int(w * fx0), int(h * fy0), int(w * fx1), int(h * fy1)


def _single_diff_peak(
    base_png: bytes,
    frame_png: bytes,
    *,
    thr: int = 40,
    win: int = 12,
    region: tuple[int, int, int, int] | None = None,
):
    """Cursor position in ``frame`` vs a cursor-free ``base`` (one diff, fast).

    ``region`` = (x0, y0, x1, y1) restricts the diff to a sub-rectangle (a
    quadrant) — cheaper and immune to churn outside it. Coords returned are in
    full-frame space.
    """
    import numpy as np

    base, w, h = _png_to_gray(base_png)
    frame, _, _ = _png_to_gray(frame_png)
    if base.shape != frame.shape:
        return None
    ox, oy = 0, 0
    if region is not None:
        x0, y0, x1, y1 = region
        ox, oy = max(0, x0), max(0, y0)
        base = base[oy:y1, ox:x1]
        frame = frame[oy:y1, ox:x1]
        if base.size == 0:
            return None
    d = np.abs(frame - base).astype(np.float64)
    d[d < thr] = 0.0
    if not d.any():
        return None
    integ = np.pad(d.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    box = integ[win:, win:] - integ[:-win, win:] - integ[win:, :-win] + integ[:-win, :-win]
    if box.size == 0:
        return None
    py, px_ = np.unravel_index(int(np.argmax(box)), box.shape)
    sub = d[py:py + win, px_:px_ + win]
    sy, sx = np.nonzero(sub)
    if sy.size == 0:
        return None
    wts = sub[sy, sx]
    cx = ox + px_ + float((sx * wts).sum() / wts.sum())
    cy = oy + py + float((sy * wts).sum() / wts.sum())
    return int(round(cx)), int(round(cy))


def find_cursor_by_quadrant(
    base_png: bytes,
    frame_png: bytes,
    *,
    expected_quadrant: str | None = None,
    thr: int = 40,
) -> tuple[int, int, str] | None:
    """Locate the cursor one quadrant at a time, most-probable first.

    Implements the "analyse a single quarter, follow the cursor" strategy:
    never diff the whole frame at once. Try ``expected_quadrant`` first (where
    the cursor was just commanded), then the rest in dock-order; return the
    first quadrant with a clean peak. ~4x cheaper per quadrant, and a live
    region in another quadrant is simply never looked at. Returns
    (x, y, quadrant) in full-frame coords.
    """
    _, w, h = _png_to_gray(frame_png)
    order: list[str] = []
    if expected_quadrant in _QUADRANTS:
        order.append(expected_quadrant)
    order.extend(q for q in _QUADRANT_ORDER if q not in order)
    for quad in order:
        region = _quadrant_box_px(quad, w, h)
        found = _single_diff_peak(base_png, frame_png, thr=thr, region=region)
        if found is not None:
            return found[0], found[1], quad
    return None


@dataclass
class PointerAffine:
    """Measured axis-aligned mapping capture-pixel → ydotool-global for a source.

    global = (local - bx)/ax  is the inverse used to aim; stored forward as
    local = ax*global + bx so it's easy to validate.
    """

    ax: float
    bx: float
    ay: float
    by: float
    source: str
    ok: bool
    samples: int = 0
    # "known zero" anchor: the capture pixel the cursor clamps to when slammed
    # into a screen corner, plus the ydotool command that reaches it. A reliable,
    # UI-independent reference the caller can always re-establish.
    anchor_corner: str | None = None
    anchor_local: tuple[int, int] | None = None
    anchor_command: tuple[int, int] | None = None
    residual_px: float | None = None

    def global_for_local(self, lx: float, ly: float) -> tuple[int, int]:
        gx = (lx - self.bx) / (self.ax or 1.0)
        gy = (ly - self.by) / (self.ay or 1.0)
        return int(round(gx)), int(round(gy))

    def to_dict(self) -> dict[str, Any]:
        return {
            "ax": round(self.ax, 5), "bx": round(self.bx, 2),
            "ay": round(self.ay, 5), "by": round(self.by, 2),
            "source": self.source, "ok": self.ok, "samples": self.samples,
            "anchor_corner": self.anchor_corner,
            "anchor_local": list(self.anchor_local) if self.anchor_local else None,
            "anchor_command": list(self.anchor_command) if self.anchor_command else None,
            "residual_px": round(self.residual_px, 1) if self.residual_px is not None else None,
        }


# ydotool command far beyond any real screen, per corner: the compositor clamps
# the pointer to that screen corner, giving a guaranteed known reference.
_CORNER_COMMANDS: dict[str, tuple[int, int]] = {
    "tl": (-1_000_000, -1_000_000),
    "tr": (1_000_000, -1_000_000),
    "bl": (-1_000_000, 1_000_000),
    "br": (1_000_000, 1_000_000),
}


def park_at_corner(
    source: str,
    corner: str = "tl",
    *,
    move: MoveFn,
    capture: CaptureFn,
    settle: Callable[[], None] | None = None,
) -> tuple[int, int] | None:
    """Slam the pointer into a screen ``corner`` (the compositor clamps it there)
    and return where it landed in capture pixels — the "known zero" reference.

    Reading the pointer position is blocked on Wayland; ESTABLISHING a known one
    by clamping to a corner is not. The corner is unambiguous (no UI element
    sits exactly at a screen corner) so the move-and-diff detector locks onto
    the cursor cleanly.
    """
    cmd = _CORNER_COMMANDS.get(corner, _CORNER_COMMANDS["tl"])
    # baseline with the cursor at the OPPOSITE corner so the diff is clean
    opp = {"tl": "br", "tr": "bl", "bl": "tr", "br": "tl"}[corner]
    move(*_CORNER_COMMANDS[opp])
    if settle is not None:
        settle()
    base = capture(source)
    move(*cmd)
    if settle is not None:
        settle()
    frame = capture(source)
    if not base or not frame:
        return None
    found = find_cursor_by_quadrant(base, frame, expected_quadrant=corner)
    return (found[0], found[1]) if found else None


def detect_live_quadrants(
    source: str,
    *,
    capture: CaptureFn,
    settle: Callable[[], None] | None = None,
    change_frac: float = 0.002,
    thr: int = 30,
) -> set[str]:
    """Quadrants whose content changes on its own (a terminal/animation).

    Two captures with NO pointer move; any quadrant with a meaningful diff is
    "live". Calibration then avoids placing probes there so churn can't poison
    the cursor detection.
    """
    import numpy as np

    if settle is not None:
        settle()
    f1 = capture(source)
    if settle is not None:
        settle()
    f2 = capture(source)
    if not f1 or not f2:
        return set()
    a, w, h = _png_to_gray(f1)
    b, _, _ = _png_to_gray(f2)
    if a.shape != b.shape:
        return set()
    d = (np.abs(a - b) >= thr)
    live: set[str] = set()
    for quad in _QUADRANT_ORDER:
        x0, y0, x1, y1 = _quadrant_box_px(quad, w, h)
        cell = d[y0:y1, x0:x1]
        if cell.size and cell.mean() >= change_frac:
            live.add(quad)
    return live


def _fit_affine_robust(gs: list[float], ls: list[float]) -> tuple[float, float]:
    """Least-squares slope/intercept with one round of residual outlier drop."""
    import numpy as np

    g = np.array(gs, float)
    l = np.array(ls, float)
    a, b = np.polyfit(g, l, 1)
    if len(g) >= 4:
        resid = np.abs(l - (a * g + b))
        med = float(np.median(resid)) or 1.0
        keep = resid <= 3.0 * med
        if keep.sum() >= 2 and keep.sum() < len(g):
            a, b = np.polyfit(g[keep], l[keep], 1)
    return float(a), float(b)


def calibrate_pointer_affine(
    source: str,
    *,
    move: MoveFn,
    capture: CaptureFn,
    probes: list[tuple[int, int]] | None = None,
    park_global: tuple[int, int] = (32000, 32000),
    settle: Callable[[], None] | None = None,
    avoid_live_quadrants: bool = True,
    probe_grid: tuple[int, int] | None = None,
    global_bounds: tuple[int, int, int, int] | None = None,
    anchor_corner: str | None = "tl",
) -> PointerAffine:
    """Measure the ydotool→capture mapping ONCE with N+1 captures, then cache it.

    Fast alternative to per-click closed-loop: park the cursor off-source for a
    clean base (1 capture), move to each probe global and diff against the base
    (1 capture each) to observe the cursor's capture pixel, then least-squares
    solve the axis-aligned affine local = a·global + b. All future clicks reuse
    the cached affine open-loop — zero captures per click.
    """
    def _settle() -> None:
        if settle is not None:
            settle()

    # Which capture quadrants have live content? Avoid probing into them.
    live = detect_live_quadrants(source, capture=capture, settle=settle) if avoid_live_quadrants else set()

    # Build a probe grid spread across the global space; each probe is tagged
    # with the capture quadrant it is expected to land in (orientation-preserving
    # rough correspondence). Drop probes whose expected quadrant is live.
    if probes is None:
        gx0, gy0, gx1, gy1 = global_bounds or (700, 500, 2800, 2000)
        nx, ny = probe_grid or (3, 3)
        cxg, cyg = (gx0 + gx1) / 2, (gy0 + gy1) / 2
        probes = []
        for iy in range(ny):
            for ix in range(nx):
                px = int(gx0 + (gx1 - gx0) * (ix / max(1, nx - 1)))
                py = int(gy0 + (gy1 - gy0) * (iy / max(1, ny - 1)))
                probes.append((px, py))
    else:
        cxg = (min(p[0] for p in probes) + max(p[0] for p in probes)) / 2
        cyg = (min(p[1] for p in probes) + max(p[1] for p in probes)) / 2

    def _expected_quad(gx: int, gy: int, bw: int, bh: int) -> str:
        return quadrant_of_local(0 if gx < cxg else bw, 0 if gy < cyg else bh, bw or 1, bh or 1)

    move(*park_global)
    _settle()
    base = capture(source)
    bw, bh = (_png_to_gray(base)[1:] if base else (0, 0))

    gxs, lxs, gys, lys, used = [], [], [], [], 0
    for gx, gy in probes:
        quad = _expected_quad(gx, gy, bw, bh) if bw and bh else None
        if quad is not None and quad in live:
            continue  # skip probes that would land in a live (noisy) quadrant
        move(gx, gy)
        _settle()
        frame = capture(source)
        region = _quadrant_box_px(quad, bw, bh) if (quad and bw and bh) else None
        found = _single_diff_peak(base, frame, region=region)
        if found is None:
            continue
        lx, ly = found
        gxs.append(gx); lxs.append(lx)
        gys.append(gy); lys.append(ly)
        used += 1
    if used < 2:
        return PointerAffine(1.0, 0.0, 1.0, 0.0, source, ok=False, samples=used)
    ax, bx = _fit_affine_robust(gxs, lxs)
    ay, by = _fit_affine_robust(gys, lys)
    aff = PointerAffine(ax, bx, ay, by, source, ok=True, samples=used)

    # "known zero" anchor + validation: park at a corner (a guaranteed known
    # reference reading can't give us on Wayland) and check the fitted affine
    # predicts it. A large residual flags a bad calibration instead of a silent
    # mis-click. The corner command is a clamped/saturated point, so it anchors
    # + validates but is NOT fed into the linear fit.
    if anchor_corner:
        obs = park_at_corner(source, anchor_corner, move=move, capture=capture, settle=settle)
        if obs is not None and bw and bh:
            aff.anchor_corner = anchor_corner
            aff.anchor_local = obs
            aff.anchor_command = _CORNER_COMMANDS.get(anchor_corner)
            # soft validation: the clamp command is saturated (its magnitude
            # can't be a linear fit point), but the cursor MUST land in that
            # corner's quadrant. residual = distance from the exact screen
            # corner, a quality signal; wrong quadrant flags a bad calibration.
            fx0, fy0, fx1, fy1 = _QUADRANTS[anchor_corner]
            corner_px = (int(bw * (0 if fx0 == 0 else 1)), int(bh * (0 if fy0 == 0 else 1)))
            aff.residual_px = math.hypot(obs[0] - corner_px[0], obs[1] - corner_px[1])
            if quadrant_of_local(obs[0], obs[1], bw, bh) != anchor_corner:
                aff.ok = False  # cursor didn't clamp to the expected corner
    return aff


class CoordinateValidationMonitor:
    """Append-only record + summary of mapping validations (the monitoring layer).

    Tracks mapping accuracy over time so drift or a regression in the coordinate
    math surfaces as a rising error rate rather than a silent mis-click.
    """

    def __init__(self, log_path: str | Path | None = None, *, clock: _Clock | None = None) -> None:
        self._records: list[dict[str, Any]] = []
        self._log_path = Path(log_path) if log_path else None
        self._clock = clock

    def record(self, validation: MappingValidation, *, ts: float | None = None) -> dict[str, Any]:
        entry = validation.to_dict()
        if ts is None and self._clock is not None:
            ts = self._clock()
        entry["ts"] = ts
        self._records.append(entry)
        if self._log_path is not None:
            with self._log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry) + "\n")
        return entry

    def summary(self) -> dict[str, Any]:
        n = len(self._records)
        if n == 0:
            return {"count": 0, "success_rate": None, "mean_error_px": None, "max_error_px": None, "by_source": {}}
        oks = [r for r in self._records if r.get("ok")]
        errs = [r["error_px"] for r in self._records if r.get("error_px") is not None]
        off_monitor = [r for r in self._records if not r.get("on_expected_monitor")]
        by_source: dict[str, dict[str, Any]] = {}
        for r in self._records:
            s = by_source.setdefault(r["source"], {"count": 0, "ok": 0})
            s["count"] += 1
            s["ok"] += 1 if r.get("ok") else 0
        return {
            "count": n,
            "success_rate": round(len(oks) / n, 3),
            "mean_error_px": round(sum(errs) / len(errs), 1) if errs else None,
            "max_error_px": round(max(errs), 1) if errs else None,
            "off_monitor_count": len(off_monitor),
            "by_source": by_source,
        }
