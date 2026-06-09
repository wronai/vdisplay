# vdisplay API contract

Stable command and response model shared by CLI, DSL (`dsl2vdisplay`), REST (`rest2vdisplay`), MCP, and the local broker (`vdisplay-agent`).

## Command model

All interfaces normalize to `CommandRequest` (`src/vdisplay/application/commands.py`):

| Field | Role |
|-------|------|
| `verb` | `HEALTH`, `MONITORS`, `WINDOWS`, `ALL`, `SCREENSHOT`, `VIRTUAL_START`, `MIRROR`, `ADOPT`, `RELEASE`, … |
| `display` | X11 display (e.g. `:0`, `:99`) |
| `apps_only` / `include_all` | Window/monitor filtering |
| `match_class`, `match_pid`, `match_app` | Window filters |
| `output`, `width`, `height`, `source`, `target` | Capture / session parameters |

DSL dicts map via `CommandRequest.from_dsl(cmd, line=...)`.

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

On failure:

```json
{
  "ok": false,
  "action": "screenshot",
  "data": {},
  "meta": { "route": "local", "agent_url": "" },
  "error": {
    "code": "backend_unavailable",
    "message": "Driver-level capture failed.",
    "details": {}
  }
}
```

### Error codes

| Code | Meaning |
|------|---------|
| `not_supported` | Capability not available on this platform/session |
| `dependency_missing` | Required system tool or Python package missing |
| `permission_required` | DRM/fbdev/portal permission denied |
| `session_not_found` | Broker session id unknown or expired |
| `invalid_request` | Bad parameters or `VDisplayError` |
| `backend_unavailable` | Capture or backend could not produce a frame |
| `internal` | Unexpected failure |

## Execution policy

Single decision point: `ExecutionPolicy` in `src/vdisplay/application/runtime.py`.

| Condition | Route |
|-----------|--------|
| `VDISPLAY_AGENT_URL` set | `agent` (canonical production path) |
| `VDISPLAY_AGENT_BROKER=1` (inside broker process) | `local` |
| `CommandRequest.local_only=True` | `local` |
| No agent URL | `local` (developer / test fallback) |

All routing goes through `application.executor.execute()`.

## Agent HTTP surface (vdisplay-agent)

Broker responses use the same envelope as `CommandResult` (`packages/vdisplay-agent/src/vdisplay_agent/envelope.py`). `AgentClient` flattens `data` to the top level for SDK backward compatibility.

Broker endpoints (frozen; `packages/vdisplay-agent/src/vdisplay_agent/schemas.py`):


| Method | Path | Command verb |
|--------|------|----------------|
| GET | `/health` | `HEALTH` |
| GET | `/capabilities` | `CAPABILITIES` |
| GET | `/diagnostics` | `VALIDATE` (partial) |
| GET | `/outputs` | `MONITORS` |
| GET | `/windows` | `WINDOWS` |
| POST | `/session/virtual/start` | `VIRTUAL_START` |
| POST | `/session/mirror/start` | `MIRROR` |
| POST | `/session/relay/start` | relay session |
| POST | `/session/{id}/stop` | session stop |
| POST | `/capture/frame` | `SCREENSHOT` |
| POST | `/window/adopt` | `ADOPT` |
| POST | `/window/release` | `RELEASE` |

REST control layer (`rest2vdisplay`) should converge on `POST /v1/command` with the same envelope (planned).

## DSL mapping

```
MONITORS DISPLAY :0     → CommandVerb.MONITORS
WINDOWS DISPLAY :0 APPS_ONLY → CommandVerb.WINDOWS, apps_only=true
SCREENSHOT OUT x.png DISPLAY :99 → CommandVerb.SCREENSHOT
ADOPT APP Firefox       → CommandVerb.ADOPT
```

`dsl2vdisplay` `DslResult` is produced via `CommandResult.to_dsl_result()`.
