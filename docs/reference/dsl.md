# DSL reference

**Package:** `packages/dsl2vdisplay` · **Entry:** `dsl2vdisplay -c 'VERB ...'`

## Flow

```
dsl2vdisplay → CommandRequest → application.executor → local | agent
```

When `VDISPLAY_AGENT_URL` is set, commands route to the broker. See [guides/agent-broker.md](../guides/agent-broker.md).

## Query verbs

`HEALTH`, `INFO`, `OUTPUTS`, `MONITORS`, `WINDOWS`, `ALL`, `CAPABILITIES`, `VALIDATE`, `CONTROLS_LIST`, `CONTROLS_FIND`

## Command verbs

`SCREENSHOT`, `VIRTUAL_START`, `VIRTUAL_STOP`, `LAUNCH`, `MIRROR`, `ADOPT`, `RELEASE`, `TERMINAL_OPEN`, `BROWSER_OPEN`, `CONTROL_CLICK`, `CONTROL_FOCUS`, `CONTROL_SET_VALUE`, `DIAGNOSE_CONTROL`

## Examples

```bash
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765

dsl2vdisplay -c 'MONITORS DISPLAY :0'
dsl2vdisplay -c 'WINDOWS DISPLAY :0'
dsl2vdisplay -c 'SCREENSHOT OUT /tmp/vd.png DISPLAY :99'
dsl2vdisplay -c 'BROWSER_OPEN URL https://example.com SESSION_ID web-1'
dsl2vdisplay -c 'CONTROL_CLICK BACKEND browser SESSION_ID web-1 SELECTOR "#go" VERIFY true'
```

## Related adapters

| Adapter | Doc |
|---------|-----|
| `nlp2vdisplay` | NL → DSL — [packages/README.md](../../packages/README.md) |
| `uri2vdisplay` | `vdisplay://cmd/...` |
| `cli2vdisplay` | REPL |

Install: `pip install -e packages/dsl2vdisplay`
