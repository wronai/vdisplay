# CI agent screenshot

Simulates a CI/agent workflow: start virtual display, optionally launch a GUI app, capture frames.

- Docs: [docs/examples.md](../../docs/examples.md)
- Docker guide: [docs/docker-guide.md](../../docs/docker-guide.md)

## Run

```bash
cd examples/ci-agent
docker compose run --rm ci-agent
```

Frames are saved to `output/frame-000.png`, `output/frame-001.png`, …

On a **desktop host** with GUI apps, consider [examples/agent-broker](../agent-broker/) instead — virtual capture still works in-process, but the broker centralizes sessions for multiple clients.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VD_FRAMES` | `3` | Number of screenshots |
| `VD_WIDTH` | `1920` | Virtual display width |
| `VD_HEIGHT` | `1080` | Virtual display height |
| `VD_LAUNCH` | *(empty)* | Optional command to launch (e.g. `xclock`) |

## GitHub Actions snippet

```yaml
- name: Agent screenshot
  run: |
    cd examples/ci-agent
    docker compose run --rm ci-agent
- uses: actions/upload-artifact@v4
  with:
    name: screenshots
    path: examples/ci-agent/output/
```

See [agent.py](agent.py).
