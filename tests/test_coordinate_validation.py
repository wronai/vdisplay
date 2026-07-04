"""Hermetic tests for the coordinate-validation monitoring layer.

Synthetic captures render a fake cursor over noisy background so the detector,
validator, adaptive loop, and monitor are exercised without any hardware.
"""
from __future__ import annotations

import io

import pytest

np = pytest.importorskip("numpy")
Image = pytest.importorskip("PIL.Image")

from vdisplay.capture.coordinate_validation import (
    CoordinateValidationMonitor,
    MappingValidation,
    converge_pointer_to_local,
    locate_cursor,
    probe_pointer_scale,
    validate_pointer_mapping,
    which_monitor_has_cursor,
)


class FakeDesktop:
    """A monitor whose capture is (global - offset) / scale, with a drawn cursor
    and per-frame background noise (a live 'terminal')."""

    def __init__(self, *, offset=(0, 0), scale=1.0, size=(400, 300), noisy=False, cap_w=None, cap_h=None):
        self.offset = offset
        self.scale = scale
        self.size = size  # capture pixel size
        self.noisy = noisy
        self.pointer = (0, 0)
        self._tick = 0

    def move(self, gx, gy):
        self.pointer = (gx, gy)

    def _cursor_local(self):
        lx = (self.pointer[0] - self.offset[0]) / self.scale
        ly = (self.pointer[1] - self.offset[1]) / self.scale
        return lx, ly

    def capture(self, _source):
        w, h = self.size
        # deterministic base background
        arr = np.full((h, w), 20, dtype=np.uint8)
        if self.noisy:
            # a 'live terminal': a band that flips pattern every frame
            self._tick += 1
            band = (np.arange(w) + self._tick * 7) % 2 * 120
            arr[40:70, :] = band.astype(np.uint8)
        lx, ly = self._cursor_local()
        if 0 <= lx < w and 0 <= ly < h:
            x0, y0 = int(lx), int(ly)
            arr[max(0, y0):y0 + 12, max(0, x0):x0 + 8] = 240  # bright cursor block
        buf = io.BytesIO()
        Image.fromarray(arr, mode="L").save(buf, format="PNG")
        return buf.getvalue()


def test_locate_cursor_clean():
    d = FakeDesktop(offset=(0, 0), scale=1.0)
    loc = locate_cursor("DP-1", (150, 120), move=d.move, capture=d.capture)
    assert loc is not None
    assert abs(loc.x - 150) <= 6 and abs(loc.y - 120) <= 6
    assert loc.confidence > 0


def test_locate_cursor_survives_live_background():
    # noisy 'terminal' band must not defeat the presence-consistency detector
    d = FakeDesktop(offset=(0, 0), scale=1.0, noisy=True)
    loc = locate_cursor("DP-1", (200, 150), move=d.move, capture=d.capture)
    assert loc is not None
    assert abs(loc.x - 200) <= 8 and abs(loc.y - 150) <= 8


def test_which_monitor_has_cursor_picks_the_right_one():
    dp1 = FakeDesktop(offset=(0, 0), scale=1.0)          # cursor lands here for small globals
    dp2 = FakeDesktop(offset=(5000, 0), scale=1.0)       # far away; cursor never visible
    caps = {"DP-1": dp1, "DP-2": dp2}

    def move(x, y):
        dp1.move(x, y)
        dp2.move(x, y)

    def capture(src):
        return caps[src].capture(src)

    mon, loc = which_monitor_has_cursor((150, 120), ["DP-1", "DP-2"], move=move, capture=capture)
    assert mon == "DP-1"
    assert loc is not None


def test_probe_pointer_scale_recovers_scale():
    d = FakeDesktop(offset=(100, 50), scale=2.0)  # 2 global units per capture px
    scale = probe_pointer_scale("DP-1", move=d.move, capture=d.capture, anchor_global=(300, 250), step_units=100)
    assert scale.ok
    assert abs(scale.units_per_px_x - 2.0) < 0.4
    assert abs(scale.units_per_px_y - 2.0) < 0.4


def test_validate_pointer_mapping_flags_offset_error():
    # The desktop has a real +80px x-offset the mapping doesn't know about
    # (region origin 0) -> the cursor lands 80px off target.
    d = FakeDesktop(offset=(80, 40), scale=1.0, size=(400, 300))
    meta = {"source": "TESTMON", "region": {"x": 0, "y": 0, "width": 400, "height": 300}, "width": 400, "height": 300}
    v = validate_pointer_mapping((200, 150), meta, "TESTMON", move=d.move, capture=d.capture, tolerance_px=20)
    assert v.observed_local is not None
    assert not v.ok  # ~89px off
    assert v.error_px and v.error_px > 20


def test_converge_pointer_corrects_offset_error():
    # same unknown offset, but the adaptive loop measures + corrects it
    d = FakeDesktop(offset=(80, 40), scale=1.0, size=(400, 300))
    meta = {"source": "TESTMON", "region": {"x": 0, "y": 0, "width": 400, "height": 300}, "width": 400, "height": 300}
    res = converge_pointer_to_local((200, 150), meta, "TESTMON", move=d.move, capture=d.capture, tolerance_px=15, max_iters=8)
    assert res.ok, res.to_dict()
    assert res.final_error_px is not None and res.final_error_px <= 15


def test_monitor_summary_tracks_accuracy(tmp_path):
    log = tmp_path / "coordval.jsonl"
    mon = CoordinateValidationMonitor(log, clock=lambda: 123.0)
    good = MappingValidation("DP-1", (10, 10), (10, 10), (12, 11), 2.2, True, 0.9, True)
    bad = MappingValidation("DP-1", (10, 10), (10, 10), (90, 90), 113.0, True, 0.8, False)
    mon.record(good)
    mon.record(bad)
    s = mon.summary()
    assert s["count"] == 2
    assert s["success_rate"] == 0.5
    assert s["max_error_px"] == 113.0
    assert s["by_source"]["DP-1"] == {"count": 2, "ok": 1}
    # persisted with timestamp
    lines = log.read_text().strip().splitlines()
    assert len(lines) == 2
    assert '"ts": 123.0' in lines[0]


def test_off_monitor_recorded_when_cursor_absent():
    d = FakeDesktop(offset=(0, 0), scale=1.0, size=(400, 300))
    # target maps to a global that renders off-capture (cursor never visible)
    meta = {"source": "DP-1", "region": {"x": 0, "y": 0, "width": 400, "height": 300}}
    v = validate_pointer_mapping((9999, 9999), meta, "DP-1", move=d.move, capture=d.capture)
    assert not v.on_expected_monitor
    assert not v.ok
    assert v.observed_local is None


def _frame_with_cursor(w, h, cx, cy, noisy=False, tick=0):
    """A static grayscale PNG with a synthetic arrow cursor drawn at (cx, cy)."""
    arr = np.full((h, w), 20, dtype=np.uint8)
    if noisy:
        band = (np.arange(w) + tick * 7) % 2 * 120
        arr[40:70, :] = band.astype(np.uint8)
    # draw an arrow matching the default template shape
    th, tw = 22, 16
    for y in range(th):
        span = int(tw * (1 - y / th))
        for x in range(min(span, tw)):
            yy, xx = cy + y, cx + x
            if 0 <= yy < h and 0 <= xx < w:
                arr[yy, xx] = 30 if (x == 0 or x == span - 1 or y == th - 1) else 235
    buf = io.BytesIO()
    Image.fromarray(arr, mode="L").save(buf, format="PNG")
    return buf.getvalue()


def test_locate_cursor_in_single_static_frame():
    from vdisplay.capture.coordinate_validation import locate_cursor_in_frame

    png = _frame_with_cursor(300, 240, 180, 90)
    loc = locate_cursor_in_frame(png, "DP-1")
    assert loc is not None
    assert loc.method == "template"
    # center of a 16x22 arrow drawn at (180,90) -> ~ (188, 101)
    assert abs(loc.x - (180 + 8)) <= 4
    assert abs(loc.y - (90 + 11)) <= 4


def test_single_frame_detection_over_live_background():
    from vdisplay.capture.coordinate_validation import locate_cursor_in_frame

    png = _frame_with_cursor(300, 240, 200, 150, noisy=True, tick=3)
    loc = locate_cursor_in_frame(png, "DP-1")
    assert loc is not None
    assert abs(loc.x - 208) <= 5 and abs(loc.y - 161) <= 5


def test_single_frame_search_region_scopes_match():
    from vdisplay.capture.coordinate_validation import locate_cursor_in_frame

    png = _frame_with_cursor(300, 240, 40, 30)
    # restrict search to the right half; the cursor (left) must not be found
    loc = locate_cursor_in_frame(png, "DP-1", search_region=(150, 0, 300, 240))
    assert loc is None


def test_single_frame_none_when_absent():
    from vdisplay.capture.coordinate_validation import locate_cursor_in_frame

    blank = _frame_with_cursor(120, 100, -999, -999)  # no cursor drawn on-frame
    assert locate_cursor_in_frame(blank, "DP-1", threshold=0.6) is None
