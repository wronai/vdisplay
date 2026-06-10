# Start here

Single entry point for vdisplay — install, choose runtime, run first commands.

Back to [documentation index](index.md)

## What vdisplay does

Cross-platform **virtual display orchestration** and **UI control** for agents, CI, and desktop automation. One API (`CommandRequest` → `executor`) powers CLI, DSL, REST, MCP, and the local **vdisplay-agent** broker.

| Layer | What it does |
|-------|----------------|
| **Discovery** | Monitors, windows, capabilities (`nl` descriptions) |
| **Capture** | Screenshots, screencast, virtual/mirror/relay sessions |
| **Control** | AT-SPI, browser, terminal, vision/OCR, map bounds |
| **Verify** | Semantic diff, screenshot diff, OCR, optional vision LLM |

Architecture: [architecture.md](architecture.md)

## Install

```bash
pip install -e ".[pillow,dev]"
pip install -e "packages/vdisplay-agent[serve]"
pip install -e packages/dsl2vdisplay packages/rest2vdisplay packages/mcp2vdisplay
```

System deps (Linux): [installation.md](installation.md)

## Local vs broker — which to use?

| Situation | Use |
|-----------|-----|
| Desktop host (GNOME Wayland, multi-monitor) | **Broker** — `vdisplay-agent serve` + `VDISPLAY_AGENT_URL` |
| CI / headless Docker / tests | **In-process** — no agent URL |
| Wayland screenshots | **Broker + screencast** — portal consent once, then capture |
| Control on native Wayland apps (PyCharm, canvas) | **Broker + vision/map** — see [guides/wayland-control.md](guides/wayland-control.md) |

### Broker (recommended on desktop)

```bash
# terminal 1
vdisplay-agent serve --port 8765

# terminal 2
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
vdisplay monitors
vdisplay agent screencast start    # Wayland: one-time portal pick
vdisplay screenshot -o /tmp/host.png --source DP-1
```

Guide: [guides/agent-broker.md](guides/agent-broker.md) · Full reference: [agent-broker.md](agent-broker.md)

### In-process (CI, containers)

```bash
unset VDISPLAY_AGENT_URL
vdisplay virtual start --width 1280 --height 720 --display :99
vdisplay screenshot -o screen.png --display :99
```

Example: [examples/headless-virtual](../examples/headless-virtual/)

## First commands

```bash
vdisplay all                              # monitors + windows + adopted
vdisplay monitors                         # connected displays
vdisplay windows --apps-only              # XWayland windows only
vdisplay diagnose                         # DISPLAY / deps check
vdisplay diagnose control                 # control backends + routing
```

## Choose your path

| I want to… | Go to |
|------------|-------|
| Automate PyCharm / canvas on Wayland | [guides/wayland-control.md](guides/wayland-control.md) |
| Build persistent click targets (GUI map) | [guides/gui-map-pack.md](guides/gui-map-pack.md) |
| OCR verify + vision LLM fallback | [guides/vision-fallback.md](guides/vision-fallback.md) |
| Control a web app (Playwright) | [guides/browser-control.md](guides/browser-control.md) |
| Control a terminal session | [guides/terminal-control.md](guides/terminal-control.md) |
| Run broker + REST/MCP/DSL | [guides/agent-broker.md](guides/agent-broker.md) |
| Look up env vars or CLI flags | [reference/](reference/) |
| Pick an example project | [examples.md](examples.md) |
| Fix errors | [troubleshooting.md](troubleshooting.md) |

## Hot / warm / cold (vision stack)

| Tier | Mechanism | When |
|------|-----------|------|
| **Hot** | OCR + map bounds + ydotool | Every click/set-value on `vision_only_surface` |
| **Warm** | post-action verify, map diff/refresh | After actions, before retry |
| **Cold** | OpenRouter vision LLM (`VDISPLAY_VISION_LLM_*`) | OCR verify fail, enrichment only |

Details: [guides/vision-fallback.md](guides/vision-fallback.md) · [guides/gui-map-pack.md](guides/gui-map-pack.md)

## Next steps

1. [examples/agent-broker](../examples/agent-broker/) — broker demo on host
2. [architecture.md](architecture.md) — routing, control plane, extensibility
3. [control-plane.md](control-plane.md) — providers, selector, verifier
4. [packages/README.md](../packages/README.md) — DSL, REST, MCP adapters
