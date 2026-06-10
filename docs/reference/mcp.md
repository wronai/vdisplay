# MCP reference

**Package:** `packages/mcp2vdisplay`

Requires broker: `export VDISPLAY_AGENT_URL=http://127.0.0.1:8765`

## Start

```bash
mcp2vdisplay serve
```

## Tools

| Tool | Purpose |
|------|---------|
| `vdisplay_agent_status` | Broker health / capabilities |
| `vdisplay_run_command` | Structured command |
| `vdisplay_run_dsl` | Raw DSL line |
| `vdisplay_to_dsl` | NL or URI → DSL |

All tools delegate to `dsl2vdisplay.dispatch()` → `application.executor`.

Adapter overview: [packages/README.md](../../packages/README.md) · Broker: [guides/agent-broker.md](../guides/agent-broker.md)
