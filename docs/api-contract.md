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

| Method | Path | Action id |
|--------|------|-----------|
| GET | `/health` | `health` |
| GET | `/capabilities` | `capabilities` |
| GET | `/diagnostics` | `diagnostics` |
| GET | `/outputs` | `outputs` |
| GET | `/windows` | `windows` |
| GET | `/sessions` | `sessions_list` |
| POST | `/session/virtual/start` | `virtual_start` |
| POST | `/session/mirror/start` | `mirror_start` |
| POST | `/session/relay/start` | `relay_start` |
| POST | `/session/terminal/open` | `terminal_start` |
| POST | `/session/browser/open` | `browser_start` |
| POST | `/session/screencast/start` | `screencast_start` |
| POST | `/session/screencast/stop` | `screencast_stop` |
| GET | `/session/screencast/status` | `screencast_status` |
| POST | `/session/{id}/stop` | `session_stop` |
| GET | `/tasks` | `tasks_list` |
| GET | `/tasks/{task_id}` | `task_get` |
| POST | `/tasks/{task_id}/heartbeat` | `task_heartbeat` |
| POST | `/tasks/{task_id}/stop` | `task_stop` |
| POST | `/sampler/start` | `sampler_start` |
| POST | `/sampler/stop` | `sampler_stop` |
| GET | `/sampler/status` | `sampler_status` |
| POST | `/capture/frame` | `capture_frame` |
| POST | `/window/adopt` | `window_adopt` |
| POST | `/window/release` | `window_release` |
| GET | `/control/plugins` | `control_plugins` |
| GET | `/diagnostics/control` | `control_diagnostics` |
| POST | `/controls/list` | `controls_list` |
| POST | `/controls/find` | `controls_find` |
| POST | `/control/invoke` | `control_invoke` |
| POST | `/control/focus` | `control_focus` |
| POST | `/control/set-value` | `control_set_value` |

REST control layer (`rest2vdisplay`) should converge on `POST /v1/command` with the same envelope (planned).

## DSL mapping

```
MONITORS DISPLAY :0     → CommandVerb.MONITORS
WINDOWS DISPLAY :0 APPS_ONLY → CommandVerb.WINDOWS, apps_only=true
SCREENSHOT OUT x.png DISPLAY :99 → CommandVerb.SCREENSHOT
ADOPT APP Firefox       → CommandVerb.ADOPT
```

`dsl2vdisplay` `DslResult` is produced via `CommandResult.to_dsl_result()`.
