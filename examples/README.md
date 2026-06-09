# vdisplay examples

Runnable examples for different environments. Full index: [docs/examples.md](../docs/examples.md).

## Headless (Docker only)

| Directory | Description |
|-----------|-------------|
| [headless-virtual/](headless-virtual/) | Minimal virtual display + screenshot |
| [ci-agent/](ci-agent/) | Agent/CI frame capture loop |
| [dev-workspace/](dev-workspace/) | Dev container with mounted repo |

## Host X11 required

| Directory | Description |
|-----------|-------------|
| [host-mirror/](host-mirror/) | Mirror host desktop via `xrandr` + screenshot |
| [host-relay/](host-relay/) | Move window off-screen and restore |

## Quick start

```bash
# no host display needed
cd examples/headless-virtual
docker compose up --build
ls output/screen.png

# host mirror (Linux + X11)
cd examples/host-mirror && ./run.sh
ls output/mirror.png

# host relay — CLI on host (each window/monitor has "nl" description)
vdisplay relay list-windows --apps-only
vdisplay relay adopt-window --app "JetBrains"
vdisplay relay release-window --app "JetBrains"
```

See also [docs/docker-guide.md](../docs/docker-guide.md), [docs/index.md](../docs/index.md), and [README.md](../README.md).
