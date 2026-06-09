import shutil

import pytest

from vdisplay import VirtualDisplaySession


@pytest.mark.skipif(shutil.which("Xvfb") is None, reason="Xvfb not installed")
@pytest.mark.skipif(shutil.which("xwd") is None, reason="xwd not installed")
def test_virtual_display_screenshot(tmp_path):
    display = ":198"
    session = VirtualDisplaySession.create(width=64, height=64, display=display)
    session.start()
    try:
        png = session.screenshot_bytes()
        assert png[:8] == b"\x89PNG\r\n\x1a\n"
        out = tmp_path / "screen.png"
        session.save_screenshot(str(out))
        assert out.stat().st_size > 100
    finally:
        session.stop()
