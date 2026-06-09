# Mirror host desktop

Duplicates the host primary display to a second output using `xrandr --same-as`, then captures a screenshot.

**Requires a running desktop session** with at least two monitors for mirror mode.

- Docs: [docs/agent-broker.md](../../docs/agent-broker.md) · [docs/docker-guide.md](../../docs/docker-guide.md#2-host-x11-forwarding)
- Examples: [docs/examples.md](../../docs/examples.md)

## Prerequisites

- Linux host with X11 or XWayland session
- At least two connected monitors (or one monitor that supports mirror)
- For Docker: access to `/tmp/.X11-unix` (often **black frames on Wayland** — use broker on host instead)

## Recommended — vdisplay-agent (Wayland-friendly)

```bash
# terminal 1
vdisplay-agent serve --port 8765

# terminal 2 — on GNOME Wayland, start ScreenCast once
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
curl -X POST http://127.0.0.1:8765/session/screencast/start \
  -H 'content-type: application/json' -d '{"interactive": true}'

cd examples/host-mirror
./run.sh
```

See [examples/agent-broker](../agent-broker/) for the full broker workflow.

## Run (Docker / X11)

Use `run.sh` — it fixes stale `DISPLAY=:99` from virtual screenshot tests and mounts `XAUTHORITY`:

```bash
cd examples/host-mirror
./run.sh
```

Or manually:

```bash
unset DISPLAY   # if you ran vdisplay virtual screenshot on :99
export HOST_DISPLAY=:0
export XAUTHORITY=$HOME/.Xauthority
xhost +local:docker
HOST_DISPLAY=$HOST_DISPLAY docker compose up --build
xhost -local:docker
```

Check monitors first on the host:

```bash
vdisplay monitors
# or with broker: dsl2vdisplay -c 'MONITORS'
```

Screenshot: `output/mirror.png`

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DISPLAY` | `:0` | Host X11 display |
| `VDISPLAY_AGENT_URL` | — | Route capture via broker when set |
| `VD_SOURCE` | `primary` | Mirror source monitor |
| `VD_TARGET` | *(auto)* | Target monitor (second connected) |

## Limitations

- Mirror mode shares the same desktop — no isolation.
- If only one monitor is connected, `xrandr --same-as` may fail; use [headless-virtual](../headless-virtual/) instead.
- On **Wayland**, Docker X11 capture is unreliable — use **vdisplay-agent + ScreenCast** on the host.

See [mirror_demo.py](mirror_demo.py).
