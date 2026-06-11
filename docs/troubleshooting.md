# Troubleshooting

Back to [documentation index](index.md) · [start-here.md](start-here.md) · [guides/wayland-control.md](guides/wayland-control.md)

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

- Firefox or PyCharm is not running
- **Firefox or PyCharm on Wayland native** has no X11 window — use XWayland mode (e.g. by launching the app with `env -u WAYLAND_DISPLAY -u XDG_SESSION_TYPE DISPLAY=:0 /snap/bin/pycharm-professional`) or virtual display instead
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

## GUI Map Pack / vision-only (PyCharm, Wayland)

### `map diff` shows many `missing` / `refresh_required`

Usually caused by a **full-monitor map** (400+ OCR elements) or UI scroll/layout change. Terminal/status-bar labels (`info`, `http_1_1`, `200`) drift independently of chat targets.

1. Check `recommendation` and `key_targets` in diff JSON:
   ```bash
   vdisplay map diff --map maps/pycharm-dp2.json --scope pycharm.ai_chat | jq '{recommendation, actionable, key_targets, summary}'
   ```
2. Refresh scoped region:
   ```bash
   vdisplay map refresh --map maps/pycharm-dp2.json --scope pycharm.ai_chat --output maps/pycharm-dp2.json
   ```
3. Rebuild with **scoped crop** (fewer false anchors). Use **pixel coordinates in the screencast frame**, not the placeholder `X,Y,W,H`:

   Find bounds with preview first:
   ```bash
   vdisplay control find --backend vision --text-contains "Ask" \
     --preview --preview-output /tmp/preview.png
   # note selected.bounds → build crop around the chat panel, e.g.:
   vdisplay map build --monitor DP-2 --crop-bounds 1507,1027,800,1200 \
     --region-id pycharm.ai_chat --output maps/pycharm-chat.json --min-text-len 3
   ```

`fingerprint`-only drift (bounds stable) is often cosmetic — safe to ignore if `key_targets` are `ok`.

### `set-value` fails without `--map`

On GNOME Wayland, OCR-target `set-value` may fail with `can_type=False`. Prefer map targets (uses ydotool-paste):

```bash
vdisplay control set-value --map maps/pycharm-dp2.json --target message --value "test"
```

### Screencast / map capture 400

Start agent **before** screencast, and screencast **after** agent is running:

```bash
vdisplay-agent serve &
sleep 2
vdisplay agent screencast start
```

Full guide: [vision-only-wayland.md](vision-only-wayland.md) · [gui-map-pack.md](../examples/control-plane/gui-map-pack.md)

### REST `POST /v1/dsl` returns 422

Ensure `rest2vdisplay` is up to date. Route expects raw DSL body (`text/plain`) or JSON `{"verb":"MONITORS"}`. Check broker first:

```bash
curl -s http://127.0.0.1:8216/health | jq .
curl -s -X POST http://127.0.0.1:8216/v1/dsl -H 'content-type: text/plain' -d 'HEALTH'
```

### Stale `dsl2vdisplay` / wrong agent routing

Symptoms: `VDISPLAY_AGENT_URL` is set but DSL runs in-process; deprecation warning mentions `agent_dispatch`; tests pass locally but CLI behaves differently.

Cause: an old `dsl2vdisplay` from site-packages instead of the repo.

Fix:

```bash
pip install -e ".[pillow,dev]" -e packages/dsl2vdisplay
python3 -c "import dsl2vdisplay.bus as b; print(b.__file__)"  # should point into packages/dsl2vdisplay/src
```

## Web console

Back to [guides/web-console.md](guides/web-console.md)

### `/web` returns 404

The running broker was started from an old install. Reinstall and restart:

```bash
pip install -e "packages/vdisplay-agent[serve]"
pkill -f "vdisplay-agent serve"
vdisplay-agent serve
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8765/web
```

On a dev checkout, also set `PYTHONPATH=src:packages/vdisplay-agent/src`.

### Replay panel shows HTTP error

Check that replay routes exist (agent must be recent):

```bash
curl -s http://127.0.0.1:8765/api/web/replay/sessions | jq .
```

404 means the agent process predates the web replay API — restart after upgrade.

### Monitor tiles empty or frame capture 503

Start persistent ScreenCast on the host (portal consent once):

```bash
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
vdisplay agent screencast start
curl -s http://127.0.0.1:8765/api/web/frame/DP-1 -o /tmp/test.png
```

Pick **All Screens** or the monitor where your IDE lives (e.g. DP-1 for PyCharm calibration).

### Okna list missing PyCharm / native Wayland apps

Expected on GNOME Wayland — the console lists XWayland windows. Use vision/map control for native apps. See [guides/wayland-control.md](guides/wayland-control.md).
