# API reference

Stable command/response model shared by CLI, DSL, REST, MCP, and broker.

**Full contract:** [api-contract.md](../api-contract.md)

## CommandRequest

Defined in `src/vdisplay/application/commands.py`. Built from DSL via `CommandRequest.from_dsl(cmd, line=...)`.

| Field group | Examples |
|-------------|----------|
| Verb | `MONITORS`, `WINDOWS`, `SCREENSHOT`, `CONTROL_CLICK`, … |
| Display | `display`, `vd_display` |
| Window filters | `match_app`, `match_class`, `match_pid` |
| Capture | `output`, `width`, `height`, `source`, `target` |
| Control | `control_selector`, `control_backend`, `control_value`, verify flags |

## Execution

```python
from vdisplay.application.commands import CommandRequest
from vdisplay.application.executor import execute

result = execute(CommandRequest.from_dsl({"verb": "MONITORS"}, line="MONITORS"))
print(result.ok, result.data)
```

Routes to broker when `VDISPLAY_AGENT_URL` is set (except inside broker process).

## Response envelope

```json
{
  "ok": true,
  "action": "monitors",
  "data": { "monitor_count": 1, "monitors": [] },
  "meta": { "route": "agent", "agent_url": "http://127.0.0.1:8765" },
  "error": null
}
```

## AgentClient SDK

```python
from vdisplay.client import AgentClient

client = AgentClient("http://127.0.0.1:8765")
client.health()
client.start_screencast(interactive=True)
client.capture_frame(source="DP-1")
```

Architecture: [architecture.md](../architecture.md) · Broker HTTP: [agent-broker.md](../agent-broker.md)
