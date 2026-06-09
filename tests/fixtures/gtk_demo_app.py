#!/usr/bin/env python3
"""Minimal GTK3 demo for AT-SPI control integration tests."""

from __future__ import annotations

import os
import sys

# Must be set before GTK imports so the accessibility bridge loads.
os.environ.setdefault("GTK_A11Y", "1")
os.environ.setdefault("NO_AT_BRIDGE", "0")


def main() -> int:
    try:
        import gi

        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk
    except ImportError:
        print("GTK3 unavailable — install gir1.2-gtk-3.0", file=sys.stderr)
        return 1

    counter = {"value": 0}

    def on_increment(_button) -> None:
        counter["value"] += 1
        label.set_text(f"Count: {counter['value']}")

    window = Gtk.Window(title="vdisplay-gtk-demo")
    window.set_default_size(320, 180)
    window.connect("destroy", Gtk.main_quit)

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    box.set_margin_top(12)
    box.set_margin_bottom(12)
    box.set_margin_start(12)
    box.set_margin_end(12)
    window.add(box)

    label = Gtk.Label(label="Count: 0", name="counter-label")
    box.pack_start(label, False, False, 0)

    button = Gtk.Button(label="Increment", name="increment-button")
    button.connect("clicked", on_increment)
    box.pack_start(button, False, False, 0)

    entry = Gtk.Entry()
    entry.set_name("demo-entry")
    entry.set_placeholder_text("type here")
    box.pack_start(entry, False, False, 0)

    window.show_all()
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
