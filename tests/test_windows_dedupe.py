from vdisplay.windows import _dedupe_app_windows


def test_dedupe_prefers_application_over_mutter_frame():
    windows = [
        {
            "window_id": "1",
            "type": "frame",
            "app_label": "Toolbox",
            "process_name": "mutter-x11-fram",
            "width": 980,
            "height": 1500,
        },
        {
            "window_id": "2",
            "type": "application",
            "app_label": "Toolbox",
            "process_name": "jetbrains-toolb",
            "width": 880,
            "height": 1326,
        },
    ]
    result = _dedupe_app_windows(windows)
    assert len(result) == 1
    assert result[0]["window_id"] == "2"
