from __future__ import annotations

JUNK_TITLES = frozenset(
    {
        "",
        "mutter guard window",
        "focusproxy",
        "content window",
    }
)
JUNK_CLASS_MARKERS = (
    "mutter guard",
    "focusproxy",
    "kotlinx-coroutines",
    "sun-awt-x11-xcanvaspeer",
    "javaawtcanvas",
    "gdk-toplevel",
)
FRAME_CLASSES = frozenset({"mutter-x11-frames", "mutter"})
