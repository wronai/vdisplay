# vdisplay-agent

Localhost broker for vdisplay — sessions, discovery, and capture on the host.

Clients set `VDISPLAY_AGENT_URL` and never touch DRM, portal, or X11 capture directly.

## Install

```bash
pip install -e "packages/vdisplay-agent[serve]"
```

## Run

```bash
vdisplay-agent serve
# default http://127.0.0.1:8765

vdisplay agent serve   # same, via main vdisplay CLI
```

## Client env

```bash
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
export VDISPLAY_AGENT_TOKEN=...   # optional
```

## Endpoints

See [docs/agent-broker.md](../../docs/agent-broker.md) for the full HTTP API, capture notes, adapter examples, and systemd user unit (`packaging/systemd/vdisplay-agent.user.service`).

Quick test:

```bash
curl -s http://127.0.0.1:8765/health
curl -s http://127.0.0.1:8765/outputs | jq .monitor_count
```
