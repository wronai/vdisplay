# Examples index

Back to [documentation index](index.md) · [Docker guide](docker-guide.md) · [Agent broker](agent-broker.md) · [README.md](../README.md)

## Desktop host — vdisplay-agent (recommended)

### [agent-broker](../examples/agent-broker/)

Install the broker once; CLI, DSL, REST, and MCP share one capture/runtime via `VDISPLAY_AGENT_URL`.

```bash
cd examples/agent-broker
./run.sh
```

Or with a persistent agent:

```bash
vdisplay-agent serve --port 8765
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
python3 examples/agent-broker/broker_demo.py
```

On **GNOME Wayland**, host screenshots need a one-time ScreenCast session:

```bash
curl -X POST http://127.0.0.1:8765/session/screencast/start \
  -H 'content-type: application/json' -d '{"interactive": true}'
vdisplay screenshot -o /tmp/host.png --source DP-1
```

Files: `broker_demo.py`, `run.sh`, `README.md`

---

### [control-plane](../examples/control-plane/)

Query and interact with UI elements semantically using AT-SPI, terminal, or browser backend providers.

```bash
python3 examples/control-plane/control_demo.py
```

Files: `control_demo.py`, `README.md`

---

## Headless (no host display)

### [headless-virtual](../examples/headless-virtual/)

Minimal virtual display inside Docker: start Xvfb, capture screenshot, exit.

```bash
cd examples/headless-virtual
docker compose up --build
```

Files: `Dockerfile`, `docker-compose.yml`, `run_virtual.py`, `README.md`

---

### [ci-agent](../examples/ci-agent/)

Agent-style loop: launch a GUI app on virtual display, capture frame, suitable for CI pipelines.

```bash
cd examples/ci-agent
docker compose run --rm ci-agent
```

Files: `Dockerfile`, `docker-compose.yml`, `agent.py`, `README.md`

---

### [dev-workspace](../examples/dev-workspace/)

Development container with the repo mounted as a volume for live code changes.

```bash
cd examples/dev-workspace
docker compose run --rm dev
```

Files: `Dockerfile`, `docker-compose.yml`, `README.md`

## Host session (mirror / relay)

> Mirror and relay need a running desktop session. On **Wayland**, prefer **vdisplay-agent + ScreenCast** for screenshots — Docker X11 forwarding often yields black frames.

### [host-mirror](../examples/host-mirror/)

Mirror the host primary monitor to a second monitor (when available) and capture a screenshot.

```bash
# with broker (Wayland-friendly capture after screencast/start)
vdisplay-agent serve &
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
cd examples/host-mirror && ./run.sh

# pick monitors explicitly
VD_SOURCE=DP-2 VD_TARGET=HDMI-1 ./run.sh
```

Output: `output/mirror.png`

Files: `Dockerfile`, `docker-compose.yml`, `mirror_demo.py`, `run.sh`, `README.md`

---

### [host-relay](../examples/host-relay/)

Demonstrate adopting and releasing a window on the host session. Adopted positions persist across CLI calls.

```bash
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765   # optional broker

vdisplay windows --apps-only
vdisplay relay adopt-window --app "JetBrains"
vdisplay relay release-window --app "JetBrains"

# Docker demo (X11 sessions; black on Wayland — use ./run-host.sh)
cd examples/host-relay && ./run-host.sh
```

Files: `Dockerfile`, `docker-compose.yml`, `relay_demo.py`, `run.sh`, `run-host.sh`, `README.md`

## Quick reference

| Example | Mode | Docker | Host desktop | Broker |
|---------|------|--------|--------------|--------|
| agent-broker | broker | No | Yes | Yes |
| control-plane | control | No | Yes | Optional |
| headless-virtual | virtual | Yes | No | No |
| ci-agent | virtual | Yes | No | No |
| dev-workspace | virtual | Yes | No | No |
| host-mirror | mirror | Optional | Yes | Recommended |
| host-relay | relay | Optional | Yes | Optional |
