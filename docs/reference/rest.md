# REST reference

**Package:** `packages/rest2vdisplay` · Default port: **8216**

Requires broker: `export VDISPLAY_AGENT_URL=http://127.0.0.1:8765`

## Start

```bash
rest2vdisplay serve --port 8216 --agent-url $VDISPLAY_AGENT_URL
```

## Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/health` | GET | Adapter + broker status |
| `/capabilities` | GET | Agent capabilities |
| `/v1/dsl` | POST | DSL as JSON or `text/plain` |
| `/v1/commands` | POST | Alias for `/v1/dsl` |
| `/v1/schema` | GET | Verb schemas |

## Examples

```bash
curl -s http://127.0.0.1:8216/health | jq .

curl -s -X POST http://127.0.0.1:8216/v1/dsl \
  -H 'content-type: application/json' \
  -d '{"verb":"MONITORS"}' | jq .

curl -s -X POST http://127.0.0.1:8216/v1/dsl \
  -H 'content-type: text/plain' \
  -d 'MONITORS DISPLAY :0' | jq .
```

Full adapter docs: [packages/README.md](../../packages/README.md) · API model: [api.md](api.md)
