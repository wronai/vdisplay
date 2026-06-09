# Architecture — command execution layer

Back to [documentation index](index.md) · [Agent broker](agent-broker.md)

All interfaces (CLI, DSL, REST, MCP) share one execution path.

## Flow

```mermaid
flowchart TB
  subgraph adapters [Adapters]
    CLI[vdisplay CLI]
    DSL[dsl2vdisplay]
    REST[rest2vdisplay]
    MCP[mcp2vdisplay]
  end
  subgraph app [vdisplay application layer]
    REQ[CommandRequest]
    EXEC[executor.execute]
    LOCAL[handlers/local]
    AGH[handlers/agent]
  end
  subgraph broker [vdisplay-agent]
    RT[AgentRuntime]
  end
  CLI --> EXEC
  DSL --> REQ
  REQ --> EXEC
  REST --> DSL
  MCP --> DSL
  EXEC -->|route=local| LOCAL
  EXEC -->|route=agent| AGH
  AGH --> RT
  LOCAL --> SVC[services: discovery, capture, session]
```

## Routing

| Condition | Route | Handler |
|-----------|-------|---------|
| `VDISPLAY_AGENT_URL` set, not broker process | `agent` | `AgentClient` → HTTP |
| otherwise | `local` | `application.services.*` |

The broker sets `VDISPLAY_AGENT_BROKER=1` so it never routes back to itself.

## Key modules

| Module | Role |
|--------|------|
| `application/commands.py` | `CommandRequest`, `CommandResult`, `CommandVerb` |
| `application/executor.py` | Single entry: `execute(request)` |
| `application/handlers/local.py` | In-process use-cases |
| `application/handlers/agent.py` | Broker HTTP mapping |
| `application/services/` | discovery, capture, session, info |
| `client.py` | `AgentClient` SDK |

## Deprecated

- `vdisplay.agent_dispatch.dispatch_via_agent` — use `application.executor.execute`
- `vdisplay.cli_handlers.*` — use `application.services`

## From source (development)

Install the core package **and** adapters in editable mode so tests and CLI use the same code:

```bash
pip install -e ".[pillow,dev]"
pip install -e "packages/vdisplay-agent[serve]"
pip install -e packages/dsl2vdisplay packages/rest2vdisplay packages/mcp2vdisplay
pytest tests/ -q
```

If `dsl2vdisplay` is only installed from PyPI/site-packages, bus routing may be stale.
