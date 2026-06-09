# Docker guide

Back to [documentation index](index.md) · [Examples index](examples.md)

vdisplay works in Docker in two distinct setups:

## 1. Fully headless (recommended)

The container runs its own Xvfb display. No host GUI is required.

**Use cases:** CI agents, screenshot pipelines, isolated app testing.

| Example | Path |
|---------|------|
| Headless virtual display | [examples/headless-virtual](../examples/headless-virtual/) |
| CI agent screenshot | [examples/ci-agent](../examples/ci-agent/) |
| Dev workspace | [examples/dev-workspace](../examples/dev-workspace/) |

```bash
cd examples/headless-virtual
docker compose up --build
```

Output: `screen.png` in the example directory (via volume mount).

## 2. Host X11 forwarding

The container connects to the host X server via Unix socket. Required for **mirror** and **relay** modes.

**Use cases:** Mirror your desktop, move windows off-screen while keeping shell control.

| Example | Path |
|---------|------|
| Mirror host desktop | [examples/host-mirror](../examples/host-mirror/) |
| Relay host windows | [examples/host-relay](../examples/host-relay/) |

```bash
# allow local X connections (once per session)
xhost +local:docker

cd examples/host-mirror
DISPLAY=$DISPLAY docker compose up --build

# revoke when done
xhost -local:docker
```

### Required host mounts

```yaml
volumes:
  - /tmp/.X11-unix:/tmp/.X11-unix:rw
environment:
  - DISPLAY=${DISPLAY:-:0}
```

## Base image dependencies

All Linux Docker examples install:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb x11-apps x11-utils x11-xserver-utils xdotool \
    && rm -rf /var/lib/apt/lists/*
```

## Choosing an example

```
Need isolation?          → examples/headless-virtual
CI / GitHub Actions?     → examples/ci-agent
Local dev with hot reload? → examples/dev-workspace
Duplicate real monitor?  → examples/host-mirror  (+ X11 socket)
Hide window off-screen?  → examples/host-relay   (+ X11 socket)
```

See [examples.md](examples.md) for per-example README files.
