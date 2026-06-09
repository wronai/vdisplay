# Examples index

Back to [documentation index](index.md) · [Docker guide](docker-guide.md) · [README.md](../README.md)

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

## Host X11 (mirror / relay)

> Requires a running X11 session on the host and `xhost +local:docker`.

### [host-mirror](../examples/host-mirror/)

Mirror the host primary output to a second output (when available) and capture a screenshot.

```bash
xhost +local:docker
cd examples/host-mirror
DISPLAY=$DISPLAY docker compose up --build
xhost -local:docker
```

Files: `Dockerfile`, `docker-compose.yml`, `mirror_demo.py`, `README.md`

---

### [host-relay](../examples/host-relay/)

Demonstrate adopting and releasing a window title match on the host session.

```bash
xhost +local:docker
cd examples/host-relay
DISPLAY=$DISPLAY WINDOW_TITLE=Firefox docker compose up --build
xhost -local:docker
```

Files: `Dockerfile`, `docker-compose.yml`, `relay_demo.py`, `README.md`

## Quick reference

| Example | Mode | `docker compose` service | Output |
|---------|------|--------------------------|--------|
| headless-virtual | virtual | `virtual` | `./output/screen.png` |
| ci-agent | virtual | `ci-agent` | `./output/frame-*.png` |
| dev-workspace | virtual | `dev` | interactive shell |
| host-mirror | mirror | `mirror` | `./output/mirror.png` |
| host-relay | relay | `relay` | stdout JSON log |
