# Mirror host desktop

Duplicates the host primary display to a second output using `xrandr --same-as`, then captures a screenshot.

**Requires host X11** — this example does not work in a fully headless environment.

- Docs: [docs/docker-guide.md](../../docs/docker-guide.md#2-host-x11-forwarding)
- Examples: [docs/examples.md](../../docs/examples.md)

## Prerequisites

- Linux host with X11 session
- At least two connected outputs (or one output that supports mirror)
- Docker with access to `/tmp/.X11-unix`

## Run

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
vdisplay diagnose
vdisplay outputs
# or: dsl2vdisplay -c 'OUTPUTS DISPLAY :0'
```

Screenshot: `output/mirror.png`

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DISPLAY` | `:0` | Host X11 display |
| `VD_SOURCE` | `primary` | Mirror source output |
| `VD_TARGET` | *(auto)* | Target output (second connected) |

## Limitations

- Mirror mode shares the same desktop — no isolation.
- If only one monitor is connected, `xrandr --same-as` may fail; use [headless-virtual](../headless-virtual/) instead.

See [mirror_demo.py](mirror_demo.py).
