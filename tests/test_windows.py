from vdisplay.windows import (
    _derive_app_label,
    _is_internal_window,
    _matches_app,
    _matches_title,
    _parse_wm_class,
)


def test_parse_wm_class():
    instance, clazz = _parse_wm_class('"firefox", "Firefox"')
    assert instance == "firefox"
    assert clazz == "Firefox"


def test_derive_app_label_prefers_title():
    label = _derive_app_label(
        title="Mozilla Firefox",
        net_wm_name="",
        wm_name="",
        wm_instance="firefox",
        wm_class="Firefox",
        process_name="firefox",
    )
    assert label == "Mozilla Firefox"


def test_internal_helper_window():
    assert _is_internal_window(
        window_id="1",
        root_id="913",
        role="helper",
        wm_class="foo",
        wm_instance="foo",
        title="FocusProxy",
        net_wm_name="FocusProxy",
        width=1,
        height=1,
        pid=None,
        process_name=None,
    )


def test_matches_title_on_app_label():
    info = {"title": None, "name": "Toolbox", "app_label": "Cursor", "process_name": "cursor"}
    assert _matches_title(info, "cursor")
    assert _matches_app(info, "cursor")
