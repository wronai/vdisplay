# Relay host windows

Move a window off-screen and restore it on the host session — keeps shell control while hiding GUI.

**Requires a visible window** matching the title or app name on the current `DISPLAY`.

- Docs: [docs/agent-broker.md](../../docs/agent-broker.md) · [docs/docker-guide.md](../../docs/docker-guide.md)
- Examples: [docs/examples.md](../../docs/examples.md)

## Run on host (CLI)

Optional broker (shared runtime with other apps):

```bash
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765   # when vdisplay-agent serve is running

vdisplay all
vdisplay windows --apps-only
vdisplay relay adopt-window --app "JetBrains"
vdisplay relay list
vdisplay relay release-window --app "JetBrains"
```

Relay screenshots on **Wayland** need an active ScreenCast session in the agent — see [agent-broker.md](../../docs/agent-broker.md).

## GNOME Wayland (screenshots)

On Wayland, `DISPLAY=:0` is **XWayland**. Docker `./run.sh` forwards only the X11 socket — capture often yields **black PNGs**.

Use the host runner:

```bash
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
curl -X POST http://127.0.0.1:8765/session/screencast/start \
  -H 'content-type: application/json' -d '{"interactive": true}'

cd examples/host-relay
./run-host.sh
```

Optional: `WINDOW_APP=JetBrains ./run-host.sh`

## Run in Docker (X11 sessions only)

```bash
cd examples/host-relay
./run.sh
```

Or manually:

```bash
xhost +local:docker
cd examples/host-relay
DISPLAY=${DISPLAY:-:0} WINDOW_TITLE=Firefox docker compose up --build
xhost -local:docker
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DISPLAY` | `:0` | Host X11 display |
| `VDISPLAY_AGENT_URL` | — | Route via broker when set |
| `WINDOW_TITLE` | `xterm` | Substring match for window title |
| `WINDOW_APP` | — | Match `app_label` from `vdisplay windows` |
| `VD_TARGET` | `offscreen` | `offscreen` or monitor name |

## What it does

1. Finds a window by title or app (`vdisplay windows`, then `adopt-window`)
2. Saves geometry, moves window off-screen (`adopt_window`)
3. Waits 2 seconds
4. Restores original position (`release_window`)

Open a matching window before running (e.g. Firefox, JetBrains Toolbox, xterm).

See [relay_demo.py](relay_demo.py).
