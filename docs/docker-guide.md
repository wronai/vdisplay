# Docker guide

Back to [documentation index](index.md) · [Examples index](examples.md)

vdisplay works in Docker in two distinct setups, plus a **host broker** path for Wayland desktops:

## 1. Fully headless (recommended for CI)

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

For production desktop automation on the host (not Docker), see [examples/agent-broker](../examples/agent-broker/) and [agent-broker.md](agent-broker.md).

## 2. Host X11 forwarding (legacy / pure X11)

The container connects to the host X server via Unix socket. Used by **mirror** and **relay** Docker examples.

> On **GNOME Wayland**, forwarded X11 capture often produces black frames. Prefer [§3 Desktop host broker](#3-desktop-host-broker-no-docker) instead.

**Use cases:** Mirror your desktop, move windows off-screen while keeping shell control.

Before running mirror/relay examples, inspect the host session:

```bash
vdisplay all
vdisplay monitors
vdisplay windows --apps-only
```

| Example | Path |
|---------|------|
| Mirror host desktop | [examples/host-mirror](../examples/host-mirror/) |
| Relay host windows | [examples/host-relay](../examples/host-relay/) |

```bash
# allow local X connections (once per session)
xhost +local:docker

cd examples/host-mirror
./run.sh

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

## 3. Desktop host broker (no Docker)

Run `vdisplay-agent` on the host when you need Wayland capture, multiple clients, or one ScreenCast consent for many screenshots.

| Example | Path |
|---------|------|
| Agent broker demo | [examples/agent-broker](../examples/agent-broker/) |

```bash
pip install -e "packages/vdisplay-agent[serve]"
vdisplay-agent serve --port 8765
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
cd examples/agent-broker && ./run.sh
```

See [agent-broker.md](agent-broker.md) for ScreenCast, REST, MCP, and systemd setup.

## Base image dependencies

All Linux Docker examples install:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb x11-apps x11-utils x11-xserver-utils xdotool \
    && rm -rf /var/lib/apt/lists/*
```

## Choosing an example

```
Desktop / Wayland / multi-app? → examples/agent-broker
Need isolation?                 → examples/headless-virtual
CI / GitHub Actions?            → examples/ci-agent
Local dev with hot reload?      → examples/dev-workspace
Duplicate real monitor?         → examples/host-mirror
Hide window off-screen?         → examples/host-relay
```

See [examples.md](examples.md) for per-example README files.
