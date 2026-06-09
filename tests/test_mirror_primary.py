from __future__ import annotations

from vdisplay.backends.linux_x11_mirror import (
    _mirror_target_candidates,
    _primary_output_from_xrandr,
)


class _FakeResult:
    def __init__(self, stdout: str = "", returncode: int = 0) -> None:
        self.stdout = stdout
        self.stderr = ""
        self.returncode = returncode


def test_primary_output_from_xrandr(monkeypatch) -> None:
    stdout = "\n".join(
        [
            "DP-1 connected 4096x2560+0+1304 (normal left inverted right x axis y axis) 600mm x 340mm",
            "DP-2 connected primary 4320x7680+4096+0 (normal left inverted right x axis y axis) 600mm x 340mm",
            "HDMI-1 connected 4096x2560+0+3864 (normal left inverted right x axis y axis) 600mm x 340mm",
        ]
    )
    monkeypatch.setattr(
        "vdisplay.backends.linux_x11_mirror.run_command",
        lambda *args, **kwargs: _FakeResult(stdout=stdout),
    )

    assert _primary_output_from_xrandr(":0") == "DP-2"


def test_mirror_target_candidates_prefers_non_primary(monkeypatch) -> None:
    stdout = "DP-2 connected primary 4320x7680+4096+0\n"
    monkeypatch.setattr(
        "vdisplay.backends.linux_x11_mirror.run_command",
        lambda *args, **kwargs: _FakeResult(stdout=stdout),
    )

    outputs = ["DP-1", "DP-2", "HDMI-1"]
    candidates = _mirror_target_candidates(":0", "DP-2", outputs)

    assert candidates == ["DP-1", "HDMI-1"]
