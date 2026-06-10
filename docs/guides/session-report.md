# Session report (recorder)

> **Status:** Implemented — hook in `application.executor` (PR #1).  
> **Goal:** one directory per run with human `README.md` + machine `session.json`, fed from `application.executor` so CLI, DSL, REST, and MCP share the same audit trail.

## Quick start

```bash
export VDISPLAY_SESSION=1
export VDISPLAY_SESSION_ID=my-run   # optional slug in folder name

vdisplay --session --session-id my-run control list --backend auto
vdisplay --session control set-value --role input --value hello --verify

ls .vdisplay/*__my-run/
cat .vdisplay/*__my-run/README.md
```

Every `execute(CommandRequest)` writes under `.vdisplay/<timestamp>__<slug>/` (or `VDISPLAY_SESSION_DIR`).

## Enable (reference)

```bash
export VDISPLAY_SESSION=1
# optional slug:
export VDISPLAY_SESSION_ID=pycharm-chat
# or explicit directory:
export VDISPLAY_SESSION_DIR=.vdisplay/my-run
# or via CLI:
vdisplay --session --session-id pycharm-chat monitors
```

Every `execute(CommandRequest)` then writes under `.vdisplay/<timestamp>__.../` (or your explicit dir).

## Problem

Today vdisplay already produces rich artifacts (screenshots, preview overlays, map JSON, verify payloads), but they are scattered across temp paths, CLI flags, and ad-hoc example folders. Debugging “why vision, not AT-SPI?” or “why verify passed but paste failed?” requires correlating logs manually.

A **session recorder** collects every command step, routing decision, verify outcome, and artifact into one narrative.

## Layout

```text
.vdisplay/
  2026-06-10T10-57-12Z__local__cli/
    README.md              # human report (regenerated)
    session.json           # machine index (updated each step)
    env.json
    steps/
      0001/
        request.json
        result.json
        command.dsl.txt
        preview.png
      0002/
        ...
```

### Naming rules

| Pattern | Content |
|---------|---------|
| `{ts}_{slug}/` | `ts` = `YYYY-MM-DD_HHMM` local; `slug` = sanitized `--session-name` or app id |
| `steps/{NNN}-*` | `NNN` = zero-padded step index, monotonic per session |
| `artifacts/*` | Long-lived exports (map pack, VQL adopt, layout SVG) — copied or symlinked, not moved from source |

## Activation

### MVP (PR-1)

| Mechanism | Example |
|-----------|---------|
| Env | `VDISPLAY_SESSION_LOG_DIR=sessions/2026-06-10_1039_pycharm-chat` |
| CLI global flag | `vdisplay --session-log-dir sessions/... control click ...` |
| Auto slug | If dir unset but `VDISPLAY_SESSION=1`: create `sessions/{ts}_{hostname}/` |

Session starts on first `executor.execute()` when dir is set; `README.md` + `session.json` written after each step and on session close.

### Later

- `vdisplay session start|close|status`
- REST header `X-VDisplay-Session-Dir`
- MCP tool metadata field `session_dir`

## Data model

### `session.json` (top level)

```json
{
  "version": 1,
  "session_id": "2026-06-10_1039_pycharm-chat",
  "started_at": "2026-06-10T10:39:12+02:00",
  "updated_at": "2026-06-10T10:41:03+02:00",
  "closed_at": null,
  "meta": {
    "host": "wayland-gnome",
    "hostname": "devbox",
    "display": ":0",
    "monitor": "DP-1",
    "app": "pycharm",
    "profile": "vision-only-wayland",
    "route_default": "agent",
    "agent_url": "http://127.0.0.1:8765",
    "capture_backend": "screencast",
    "control_backend_hint": "vision",
    "env_snapshot": {
      "VDISPLAY_AGENT_URL": "...",
      "YDOTOOL_SOCKET": "/tmp/.ydotool_socket"
    }
  },
  "steps": [],
  "artifacts": [],
  "summary": {
    "total_steps": 0,
    "ok_steps": 0,
    "failed_steps": 0,
    "backends_used": [],
    "fallbacks_used": []
  }
}
```

### Step record (`steps[]` entry)

```json
{
  "index": 4,
  "step_id": "004",
  "timestamp": "2026-06-10T10:40:55+02:00",
  "duration_ms": 842,
  "input": {
    "source": "cli",
    "command": "vdisplay control set-value ...",
    "dsl": "CONTROL SET-VALUE BACKEND vision MAP maps/chat.json TARGET message VALUE \"test\" VERIFY",
    "verb": "control",
    "request": { "action": "set-value", "backend": "vision", "map": "maps/chat.json", "target": "message", "value": "test", "verify": true }
  },
  "execution": {
    "route": "local",
    "host_environment": "wayland",
    "meta": {}
  },
  "routing": {
    "backend": "vision",
    "provider": "vision",
    "reasons": ["map_target_resolved", "no_a11y_tree"],
    "score": { "vision": 0.92, "atspi": 0.1 }
  },
  "result": {
    "ok": true,
    "action": "control.set-value",
    "verified": true,
    "verify_mode": "ocr_contains",
    "verify_confidence": 0.81,
    "verify_reasons": ["ocr_rescue", "vision_fallback"],
    "fallbacks": ["ocr_rescue"]
  },
  "files": {
    "command_dsl": "steps/004-command.dsl.txt",
    "result_json": "steps/004-result.json",
    "before_png": "steps/004-before.png",
    "after_png": "steps/004-after.png",
    "diff_png": "steps/004-diff.png",
    "preview_png": null
  },
  "artifacts_inline": {
    "selector": {},
    "target": {},
    "routing": {},
    "verification": {}
  }
}
```

Fields are **best-effort**: missing PNGs are omitted from `files`, not errors.

## Module layout

```text
src/vdisplay/session/
  __init__.py          # get_session_recorder(), is_enabled()
  model.py             # SessionMeta, StepRecord, SessionDocument dataclasses + JSON serde
  artifacts.py         # copy/link PNG, JSON, SVG; stable step filenames
  report.py            # SessionRecorder + README.md generator
  context.py           # contextvars: current session dir, step index
```

### `SessionRecorder` API (sketch)

```python
class SessionRecorder:
    def __init__(self, root: Path, *, name: str | None = None): ...
    def begin_step(self, request: CommandRequest, *, source: str, command_line: str) -> StepBuilder: ...
    def attach_execution_meta(self, meta: dict) -> None: ...
    def finish_step(self, result: CommandResult, *, artifacts: StepArtifacts) -> None: ...
    def register_artifact(self, kind: str, src: Path, *, dest_name: str | None = None) -> str: ...
    def flush(self) -> None:  # rewrite session.json + README.md
    def close(self) -> None: ...
```

`StepBuilder` collects routing/verify hooks from services before `finish_step`.

## Hook points

### 1. Primary — `application.executor.execute()` (required for MVP)

**File:** `src/vdisplay/application/executor.py`

```text
execute(cmd)
  ├─ recorder = session_recorder_for(cmd)   # from env/flag/context
  ├─ step = recorder.begin_step(cmd, source=..., command_line=...)
  ├─ meta = policy.meta_for(route)
  ├─ result = _execute_local | _execute_agent
  ├─ step.attach_meta(meta)
  ├─ recorder.finish_step(result, artifacts=collect_from_result(result))
  └─ return result
```

This alone captures **every** entry path (CLI, DSL shim, REST handler, MCP broker) because all call `execute()`.

**Wire flags:** parse `--session-log-dir` / `--session-name` in root CLI parser; stash on `CommandRequest.extra` or module-level context before dispatch.

### 2. Control service — routing + verify detail

**File:** `src/vdisplay/application/services/control.py`

After `_build_action_payload()` (or inside it), if recorder active:

- push `routing.to_dict()` into current step
- push `verification.to_dict()`, `screenshot_diff`, map target metadata
- register paths from `preview_output`, verify before/after PNG bytes

Optional callback:

```python
# session/hooks.py
_on_control_payload: Callable[[dict], None] | None = None
```

Called from `_build_action_payload` return path — avoids circular imports via lazy registration in `session/__init__.py`.

### 3. Capture — screenshot paths

**File:** `src/vdisplay/application/services/capture.py` (and agent screenshot handlers)

When capture returns `{path, meta}` or raw bytes, recorder copies to `steps/{NNN}-before.png` if step is open and slot empty.

### 4. Secondary (phase 2)

| Module | Artifact |
|--------|----------|
| `control/vision_preview.py` | `preview.png`, debug JSON |
| `control/screenshot_verify.py` | `diff.png`, diff stats |
| `control/gui_map_diff.py` | drift summary in step or session artifact |
| `control/gui_map.py` export | `artifacts/map.json`, `layout.svg` |

Phase 2 uses `recorder.register_artifact()` when export paths already exist — no duplicate capture.

## README generator

Regenerated on every `flush()`. Structure:

```markdown
# Session: pycharm-chat

**Started:** 2026-06-10 10:39 · **Host:** wayland-gnome · **Display:** :0 · **Steps:** 4 (3 ok, 1 failed)

## Environment

| Key | Value |
|-----|-------|
| Profile | vision-only-wayland |
| Agent | http://127.0.0.1:8765 |
| Capture | screencast |

## Step 004 — set-value message

- **Time:** 2026-06-10T10:40:55+02:00 (842 ms)
- **Command:** `vdisplay control set-value --backend vision --map maps/chat.json --target message --value "test" --verify`
- **DSL:** `CONTROL SET-VALUE BACKEND vision MAP maps/chat.json TARGET message VALUE "test" VERIFY`
- **Route:** local · **Backend:** vision
- **Routing:** map target resolved; no usable a11y tree on canvas host.
- **Verify:** mode `ocr_contains` · confidence 0.81 · **YES** (ocr_rescue → vision_fallback)
- **Result:** ok=true · verified=true
- **Files:**
  - [before](steps/004-before.png)
  - [after](steps/004-after.png)
  - [diff](steps/004-diff.png)
  - [result.json](steps/004-result.json)

## Routing summary

- vision: 3 steps
- fallbacks: ocr_rescue (1)

## Artifacts

- [map.json](artifacts/map.json)
- [layout.svg](artifacts/layout.svg)
```

MVP: text + links only (no embedded images). Phase 2: optional `<!-- thumbnail -->` or relative `![](steps/004-before.png)` behind `VDISPLAY_SESSION_EMBED_IMAGES=1`.

## PR breakdown

### PR-1 — MVP session recorder

| Item | Detail |
|------|--------|
| Modules | `session/model.py`, `artifacts.py`, `report.py`, `context.py` |
| Hook | `executor.execute()` only |
| Storage | `session.json`, `steps/{NNN}-command.dsl.txt`, `steps/{NNN}-result.json` |
| Artifacts | Copy PNG if path present in `result.data` (`preview_path`, `screenshot`, verify diff) |
| CLI/env | `--session-log-dir`, `VDISPLAY_SESSION_LOG_DIR` |
| Tests | unit: model serde, README render, step numbering; integration: fake execute writes dir |
| Docs | this file + `docs/reference/env.md` entry |

**Non-goals PR-1:** embed images, automatic map/VQL export, REST/MCP session headers.

### PR-2 — Control + verify richness

- Hooks in `_build_action_payload`, `_execute_map_action`
- Populate `routing`, `verification`, `fallbacks` on step
- before/after/diff bytes from `VerifierPipeline`
- `preview.png` from vision preview path

### PR-3 — Session artifacts + query

- `register_artifact()` from map export / VQL adopt CLI
- `vdisplay session list|show|grep` (read-only over `sessions/`)
- Optional JSON schema export for dataset tooling

## Env / CLI reference (planned)

| Variable / flag | Purpose |
|-----------------|---------|
| `VDISPLAY_SESSION_LOG_DIR` | Absolute or repo-relative session root |
| `VDISPLAY_SESSION_NAME` | Slug suffix when auto-creating dir |
| `VDISPLAY_SESSION=1` | Auto-create under `./sessions/{ts}_{slug}/` |
| `VDISPLAY_SESSION_EMBED_IMAGES` | Embed PNG in README (PR-2+) |
| `--session-log-dir` | CLI override (same as env) |
| `--session-name` | Slug for auto dir |

## Testing strategy

1. **Unit:** `StepRecord` round-trip JSON; README sections for ok/fail/verify/fallback.
2. **Unit:** `artifacts.copy_step_file` idempotent, preserves relative paths in `session.json`.
3. **Integration:** `executor.execute(CommandRequest(...))` with `tmpdir` session dir → assert 1 step, README contains command string.
4. **Regression:** recorder disabled → zero overhead (no extra I/O); guard with `if recorder:` only.

## Open questions

1. **Agent route:** mirror agent response artifacts into session dir, or store agent URL + raw JSON only? (MVP: raw JSON in `result.json`.)
2. **Secrets:** strip env snapshot keys matching `*TOKEN*`, `*SECRET*`, `*PASSWORD*`?
3. **Concurrent sessions:** one recorder per process via `contextvars`; broker workers get dir from request header (PR-3).
4. **Retention:** document `.gitignore` for `sessions/` except curated examples.

## Related docs

- [GUI map pack](gui-map-pack.md) — map artifacts copied to `artifacts/`
- [Vision fallback](vision-fallback.md) — fallback reasons in step record
- [Env reference](../reference/env.md) — session env vars
