from vdisplay.discovery import _ROTATION_DEGREES, _parse_xrandr_query


def test_rotation_degrees_mapping():
    assert _ROTATION_DEGREES["normal"] == 0
    assert _ROTATION_DEGREES["left"] == 90
    assert _ROTATION_DEGREES["inverted"] == 180
    assert _ROTATION_DEGREES["right"] == 270


def test_parse_xrandr_query_rotation_from_sample():
    sample = """
Screen 0: minimum 16 x 16, current 8416 x 7680, maximum 32767 x 32767
DP-1 connected 4096x2560+0+1304 (normal left inverted right x axis y axis) 610mm x 350mm
DP-2 connected primary 4320x7680+4096+0 left (normal left inverted right x axis y axis) 700mm x 390mm
HDMI-1 connected 4096x2560+0+3864 (normal left inverted right x axis y axis) 300mm x 260mm
"""
    import subprocess
    from unittest.mock import patch

    class Result:
        returncode = 0
        stdout = sample
        stderr = ""

    with patch("vdisplay.discovery.run_command", return_value=Result()):
        meta = _parse_xrandr_query(":0")

    assert meta["DP-1"]["rotation"] == "normal"
    assert meta["DP-1"]["rotation_degrees"] == 0
    assert meta["DP-2"]["rotation"] == "left"
    assert meta["DP-2"]["rotation_degrees"] == 90
    assert meta["DP-2"]["primary"] is True
    assert meta["HDMI-1"]["rotation_degrees"] == 0
