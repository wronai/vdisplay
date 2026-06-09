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
| [host-mirror/](host-mirror/) | Mirror host desktop via `xrandr` |
| [host-relay/](host-relay/) | Move window off-screen and restore |

## Quick start

```bash
# no host display needed
cd examples/headless-virtual
docker compose up --build
ls output/screen.png

# host mirror (Linux + X11)
xhost +local:docker
cd examples/host-mirror
DISPLAY=$DISPLAY docker compose up --build
xhost -local:docker
```

See also [docs/docker-guide.md](../docs/docker-guide.md) and [README.md](../README.md).
