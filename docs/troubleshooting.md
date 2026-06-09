# Troubleshooting

Back to [documentation index](index.md)

## Docker mirror shows `display: ":99"` or one output

Your shell still has `DISPLAY=:99` from a prior `vdisplay virtual screenshot` test. The container inherits it and sees only the Xvfb screen.

```bash
cd examples/host-mirror
./run.sh
```

`run.sh` ustawia `DISPLAY` i `HOST_DISPLAY` automatycznie (domyślnie `:0`), nawet gdy `DISPLAY` jest puste po `unset DISPLAY`.

Or check:

```bash
vdisplay diagnose
dsl2vdisplay -c 'OUTPUTS DISPLAY :0'
```

## `vdisplay info` works, but mirror fails

### `Unknown output 'HDMI-1'. Connected: screen`

Your system has only one X11 output (often named `screen` on NVIDIA/optimus setups).

```bash
vdisplay outputs
```

Mirror mode requires **two physical or logical outputs**. With one monitor:

```bash
# use virtual display instead
vdisplay virtual screenshot -o screen.png --display :99
```

## `No window matched title: Firefox`

The window must be **open and visible** on the current `DISPLAY`.

```bash
# list application windows with pid, class, app_label
vdisplay relay list-windows --apps-only

# match by app name, class, pid or title
vdisplay relay adopt-window --app "JetBrains"
vdisplay relay adopt-window --class firefox
vdisplay relay adopt-window --pid 40024
vdisplay relay adopt-window --title "Mozilla Firefox"
```

Each window entry includes: `title`, `name`, `type`, `wm_class`, `wm_class_instance`, `window_type`, `pid`, `process_name`, `process_cmdline`, `app_label`, **`nl`** (natural-language summary).

Common causes:

- Firefox is not running
- **Firefox on Wayland native** has no X11 window — use XWayland apps or virtual display instead
- Title differs — use `--app` or `--pid` from `list-windows`

## `xwd: unable to open display`

Install `x11-apps` (provides `xwd`):

```bash
sudo apt install x11-apps
```

## `Xvfb is not installed`

```bash
sudo apt install xvfb
```

## Relay: window adopted but not restored

Adopted window positions are **persisted** in `~/.cache/vdisplay/__vdisplay_stash__-<display>.json`, so `release-window` works in a separate CLI call:

```bash
vdisplay relay adopt-window --app "JetBrains"
vdisplay relay list              # check stash
vdisplay relay release-window --app "JetBrains"
```

Match by the same flags as adopt: `--title`, `--app`, `--class`, `--pid`, `--window-id`.

For long-running automation, use the Python API:

```python
from vdisplay import WindowRelaySession

r = WindowRelaySession.create()
r.start()
wid = r.adopt_window(match_app="Firefox")
# ... work ...
r.release_window(match_app="Firefox")
r.stop()
```

## Quick diagnostic checklist

```bash
vdisplay info          # capabilities + outputs
vdisplay outputs       # monitor names for mirror
vdisplay relay list-windows   # window titles for relay
echo $DISPLAY          # should be :0 or similar
xrandr --query         # raw output list
```
