"""Hermetic tests for the RemoteDesktop portal input primitives.

The dbus/gi session setup needs hardware + a portal dialog, so it is not tested
here; the coordinate math, keysym mapping, and the focus guard ARE, with the
portal interfaces mocked.
"""
from __future__ import annotations

import sys
import types

import pytest

# stub `dbus` so _u32/_i32 don't require the real module
_dbus_stub = types.SimpleNamespace(UInt32=lambda v: ("u32", v), Int32=lambda v: ("i32", v))
sys.modules.setdefault("dbus", _dbus_stub)

from vdisplay.input.portal_remotedesktop import RemoteDesktopPortal


class _RecordingRD:
    def __init__(self):
        self.motion = []
        self.buttons = []
        self.keys = []

    def NotifyPointerMotionAbsolute(self, sess, opts, node, x, y):
        self.motion.append((int(x), int(y)))

    def NotifyPointerButton(self, sess, opts, btn, state):
        self.buttons.append((btn, state))

    def NotifyKeyboardKeysym(self, sess, opts, ks, state):
        self.keys.append((ks, state))


def _portal():
    p = RemoteDesktopPortal()
    p._session = "/s"
    p._node = 42
    p._rd = _RecordingRD()
    return p


def test_frame_to_stream_scales_buffer_to_logical():
    p = RemoteDesktopPortal()
    p._stream_size = (2048, 1280)
    # a frame buffer at 2560x1600 -> logical 2048x1280 (x0.8)
    assert p.frame_to_stream(1484, 848, frame_w=2560, frame_h=1600) == (1187, 678)
    # identity when sizes match
    assert p.frame_to_stream(100, 200, frame_w=2048, frame_h=1280) == (100, 200)


def test_type_text_emits_ascii_keysyms_press_release():
    p = _portal()
    p.type_text("ab")
    # each char: press (state 1) then release (state 0), keysym == ord
    assert p._rd.keys == [
        (("i32", ord("a")), ("u32", 1)), (("i32", ord("a")), ("u32", 0)),
        (("i32", ord("b")), ("u32", 1)), (("i32", ord("b")), ("u32", 0)),
    ]


def test_submit_sends_return_keysym():
    p = _portal()
    p.submit()
    assert p._rd.keys == [(("i32", 0xFF0D), ("u32", 1)), (("i32", 0xFF0D), ("u32", 0))]


def test_click_emits_left_button_press_release():
    p = _portal()
    p.click()
    assert p._rd.buttons == [(("i32", 272), ("u32", 1)), (("i32", 272), ("u32", 0))]


def test_type_into_input_verified_gates_on_focus(monkeypatch):
    # when verify() says the click did NOT focus the input, NO text is typed
    p = _portal()
    monkeypatch.setattr(p, "grab_frame", lambda **k: b"frame")
    typed = p.type_into_input_verified(100, 200, "secret", verify=lambda b, a: False)
    assert typed is False
    assert p._rd.keys == []  # nothing leaked


def test_type_into_input_verified_types_when_focused(monkeypatch):
    p = _portal()
    monkeypatch.setattr(p, "grab_frame", lambda **k: b"frame")
    typed = p.type_into_input_verified(100, 200, "hi", verify=lambda b, a: True, submit=True)
    assert typed is True
    assert p._rd.motion == [(100, 200)]
    assert p._rd.keys[-2:] == [(("i32", 0xFF0D), ("u32", 1)), (("i32", 0xFF0D), ("u32", 0))]
