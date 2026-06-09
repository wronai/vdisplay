# vdisplay examples

Runnable examples for different environments. Full index: [docs/examples.md](../docs/examples.md).

## Desktop host — install once

| Directory | Description |
|-----------|-------------|
| [agent-broker/](agent-broker/) | **vdisplay-agent** + CLI/DSL/REST clients via `VDISPLAY_AGENT_URL` |
| [host-mirror/](host-mirror/) | Mirror host desktop via `xrandr` + screenshot |
| [host-relay/](host-relay/) | Move window off-screen and restore |

On **GNOME Wayland**, start the agent and a ScreenCast session for host capture — see [agent-broker/](agent-broker/) and [docs/agent-broker.md](../docs/agent-broker.md).

## Headless (Docker only)

| Directory | Description |
|-----------|-------------|
| [headless-virtual/](headless-virtual/) | Minimal virtual display + screenshot |
| [ci-agent/](ci-agent/) | Agent/CI frame capture loop |
| [dev-workspace/](dev-workspace/) | Dev container with mounted repo |

## Quick start

```bash
# broker demo (host, no Docker)
cd examples/agent-broker && ./run.sh

# headless virtual (Docker)
cd examples/headless-virtual
docker compose up --build
ls output/screen.png

# host mirror (Linux + X11/Wayland with agent screencast on Wayland)
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765   # after: vdisplay-agent serve
cd examples/host-mirror && ./run.sh

# host relay — CLI on host
vdisplay all
vdisplay windows --apps-only
vdisplay relay adopt-window --app "JetBrains"
vdisplay relay release-window --app "JetBrains"
```

See also [docs/agent-broker.md](../docs/agent-broker.md), [docs/docker-guide.md](../docs/docker-guide.md), [docs/index.md](../docs/index.md), and [README.md](../README.md).
