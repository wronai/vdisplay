# Relay host windows

Move a window off-screen and restore it on the host X11 session — keeps shell control while hiding GUI.

**Requires host X11** and a visible window matching the title.

- Docs: [docs/docker-guide.md](../../docs/docker-guide.md#2-host-x11-forwarding)
- Examples: [docs/examples.md](../../docs/examples.md)

## Run

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
| `WINDOW_TITLE` | `xterm` | Substring match for window title |
| `VD_TARGET` | `offscreen` | `offscreen` or output name |

## What it does

1. Finds a window by title (`xdotool search --name`)
2. Saves geometry, moves window off-screen (`adopt_window`)
3. Waits 2 seconds
4. Restores original position (`release_window`)

Open a matching window before running (e.g. Firefox, xterm).

See [relay_demo.py](relay_demo.py).
