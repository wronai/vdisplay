# vdisplay examples

Runnable examples for different environments.

- **Index (which example for which problem):** [docs/examples.md](../docs/examples.md)
- **Docs entry:** [docs/start-here.md](../docs/start-here.md)

## Desktop host — install once

| Directory | Description |
|-----------|-------------|
| [agent-broker/](agent-broker/) | **vdisplay-agent** + CLI/DSL/REST clients via `VDISPLAY_AGENT_URL` |
| [control-plane/](control-plane/) | Semantic UI control (AT-SPI / terminal / browser) with verification |
| [control-plugin/](control-plugin/) | **PR-18** — example control provider wheel + plugin author guide |
| [control-plugin-uia/](control-plugin-uia/) | **PR-23** — Windows UIA plugin wheel (mock on Linux CI) |
| [control-plugin-ax/](control-plugin-ax/) | **PR-23** — macOS AX plugin wheel (mock on Linux CI) |
| [control-plane/vision-disambiguation.md](control-plane/vision-disambiguation.md) | **PR-24** — vision multi-match `--index` + `--vision-min-confidence` |
| [control-plane/vision-preview.md](control-plane/vision-preview.md) | **PR-25** — vision match preview overlay (`--preview`, `-o preview.png`) |
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
# control plane demo (host, no Docker)
python3 examples/control-plane/control_demo.py

# broker demo (host, no Docker)
cd examples/agent-broker && ./run.sh

# headless virtual (Docker)
cd examples/headless-virtual
docker compose up --build
ls output/screen.png

# all examples (Docker + host; Wayland uses agent for mirror/relay)
./examples/run_all_examples.sh

# host mirror — Wayland: run-host.sh + agent screencast; X11: ./run.sh (Docker)
vdisplay agent serve                              # terminal 1
vdisplay agent screencast start                   # terminal 2, once
cd examples/host-mirror && ./run-host.sh          # Wayland
# cd examples/host-mirror && ./run.sh             # X11 only

# host relay — CLI on host
vdisplay all
vdisplay windows --apps-only
vdisplay relay adopt-window --app "JetBrains"
vdisplay relay release-window --app "JetBrains"
```

See also [docs/agent-broker.md](../docs/agent-broker.md), [docs/docker-guide.md](../docs/docker-guide.md), [docs/index.md](../docs/index.md), and [README.md](../README.md).
