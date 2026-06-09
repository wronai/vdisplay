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
vdisplay monitors
# or: dsl2vdisplay -c 'OUTPUTS DISPLAY :0'
```

## `vdisplay info` works, but mirror fails

### `Unknown output 'HDMI-1'. Connected: screen`

Your system has only one X11 output (often named `screen` on NVIDIA/optimus setups).

```bash
vdisplay monitors
```

Mirror mode requires **two physical or logical monitors**. With one monitor:

```bash
# use virtual display instead
vdisplay virtual screenshot -o screen.png --display :99
```

## `No window matched title: Firefox`

The window must be **open and visible** on the current `DISPLAY`.

```bash
# list application windows with pid, class, app_label, nl
vdisplay windows --apps-only

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
- Title differs — use `--app` or `--pid` from `vdisplay windows`

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
vdisplay info          # capabilities + monitors
vdisplay all           # monitors + windows + adopted
vdisplay monitors      # monitor names for mirror
vdisplay windows       # window titles for relay
echo $DISPLAY          # should be :0 or similar
xrandr --query         # raw output list
```

## vdisplay-agent and capture

### `MONITORS` / `/outputs` hangs or times out

Older builds called slow window enrichment (xdotool) on every `/outputs` request. Current agent uses fast monitor listing only. Upgrade and restart:

```bash
vdisplay-agent serve --port 8765
curl -s --max-time 5 http://127.0.0.1:8765/outputs | jq .monitor_count
```

Use DSL `ALL` or agent `/windows` when you need window lists with `nl`.

### `VDISPLAY_AGENT_URL` set but CLI still runs in-process

Check that `VDISPLAY_AGENT_BROKER=1` is **not** set in your shell (that flag is for the broker process only). Verify:

```bash
curl -s $VDISPLAY_AGENT_URL/health
vdisplay agent health
```

### Host mirror screenshot times out (Wayland + NVIDIA)

Virtual display capture works; host mirror often fails without DRM/fbdev access or a portal ScreenCast session:

- Add user to `video` group for `/dev/fb0` (fbdev provider)
- NVIDIA kmsgrab via ffmpeg may still fail on proprietary drivers
- Set `VDISPLAY_CAPTURE_ALLOW_PORTAL=1` on the **agent** to opt in to portal capture (one consent per portal session)
- Etap 2: start persistent ScreenCast in the agent (`POST /session/screencast/start`), then retry host capture

Workaround for agents:

```bash
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
vdisplay virtual screenshot -o screen.png --display :99
```

### REST `POST /v1/dsl` returns 422

Ensure `rest2vdisplay` is up to date. Route expects raw DSL body (`text/plain`) or JSON `{"verb":"MONITORS"}`. Check broker first:

```bash
curl -s http://127.0.0.1:8216/health | jq .
curl -s -X POST http://127.0.0.1:8216/v1/dsl -H 'content-type: text/plain' -d 'HEALTH'
```
