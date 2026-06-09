from __future__ import annotations

from vdisplay.backends.linux_x11_relay import (
    WindowState,
    _load_stash,
    _save_stash,
    _select_adopted_for_release,
    _state_matches,
)


def _toolbox_states() -> dict[str, WindowState]:
    return {
        "8388615": WindowState(
            window_id="8388615",
            title="Toolbox",
            x=4470,
            y=298,
            width=880,
            height=1326,
            app_label="Toolbox",
            pid=32977,
            wm_class="jetbrains-toolbox",
        ),
        "12582916": WindowState(
            window_id="12582916",
            title="Toolbox",
            x=4370,
            y=50,
            width=980,
            height=1500,
            app_label="Toolbox",
            pid=33544,
            wm_class="mutter-x11-frames",
        ),
    }


def test_state_matches_app_jetbrains() -> None:
    state = _toolbox_states()["8388615"]
    assert _state_matches(state, match_app="JetBrains")
    assert not _state_matches(state, match_app="Thunderbird")


def test_select_adopted_for_release_by_app_includes_frame() -> None:
    adopted = _toolbox_states()
    released = _select_adopted_for_release(adopted, match_app="JetBrains")
    assert set(released) == {"8388615", "12582916"}


def test_stash_roundtrip(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "vdisplay.backends.linux_x11_relay.Path.home",
        lambda: tmp_path,
    )
    adopted = _toolbox_states()
    _save_stash(":0", "__vdisplay_stash__", adopted)
    loaded = _load_stash(":0", "__vdisplay_stash__")
    assert loaded["8388615"].x == 4470
    assert loaded["12582916"].wm_class == "mutter-x11-frames"

    del adopted["12582916"]
    _save_stash(":0", "__vdisplay_stash__", adopted)
    loaded = _load_stash(":0", "__vdisplay_stash__")
    assert set(loaded) == {"8388615"}
