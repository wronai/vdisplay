# Full autonomy loop — observe → decide → act → verify

Roadmap and concrete commands for **GNOME Wayland multi-monitor** desktop automation without human in the loop.

Related: [gnome-wayland-screencast.md](gnome-wayland-screencast.md) · [wayland-control.md](wayland-control.md) · [dev-workflow](../../examples/dev-workflow/)

## Current state (what works)

| Layer | Status |
|-------|--------|
| **Observe** | `vdisplay screenshot --source DP-N`, img2nl/NL, `observe`, keeper multi-stream |
| **Decide** | planfile/auto, NLP (partial), app registry + map targets |
| **Act** | control vision/map (native Wayland), AT-SPI (XWayland), browser (thread-safe agent) |
| **Verify** | `--verify` on control, VerifierPipeline, retry atspi→vision |

**Gap:** `vdisplay auto` historically ran fire-and-forget commands. **Faza 1 (this iteration)** adds observe preflight + verify parsing in the auto runner.

## Architecture

```
planfile task
  → preflight_observe (screenshot + ScreenContext sidecar)   # control tasks with verify/observe
  → prepare_command (--source, --map, --verify from YAML)
  → execute (DSL / vdisplay CLI / shell)
  → finalize_result_ok (parse verified:false in JSON)
```

Single control actions already loop internally (`control.py` → VerifierPipeline → retry_policy).

## Phases

### Faza 0 — Stabilizacja (1–2 tyg.)

- `VDISPLAY_ATSPI_TIMEOUT_S=30` (default) + retry/backoff in AT-SPI provider
- Vision fallback when AT-SPI times out (`retry_policy`: atspi → vision)
- Browser control via `_run_on_browser_thread` (agent) — never sync Playwright on asyncio thread
- Test: `vdisplay control find --backend vision --vision-anchor Ask` on Cursor after `vdisplay app open cursor`

### Project config (`vdisplay.yaml`)

Each project using vdisplay should have **`vdisplay.yaml`** at the repo root with monitors, windows, actions, and automation defaults. Optional user overrides: **`.vdisplay/vdisplay.override.yaml`**.

All runtime metadata (observe PNG, VQL, context, auto run logs) goes under **`.vdisplay/`**.

```bash
vdisplay config --project .
vdisplay auto --project . --planfile examples/dev-workflow/planfile-autonomy.yaml --source yaml run
```

See [vdisplay.yaml](../../vdisplay.yaml) and [examples/dev-workflow/vdisplay.override.example.yaml](../../examples/dev-workflow/vdisplay.override.example.yaml).

### Faza 1 — Zamknięta pętla auto (milestone)

**Implemented (prototype):**

- `application/auto/feedback.py` — observe preflight, command preparation, verify parsing
- Planfile fields: `monitor`, `map`, `verify: true`, `observe: true`
- Example: [examples/dev-workflow/planfile-autonomy.yaml](../../examples/dev-workflow/planfile-autonomy.yaml)

```bash
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
export PYTHONPATH=src:packages/vdisplay-agent/src
vdisplay agent screencast start --force

vdisplay auto --project . \
  --planfile examples/dev-workflow/planfile-autonomy.yaml \
  --source yaml run
```

**Next:**

- NLP → planfile task generation with observe flags
- Task-level retry on keeper stale / AT-SPI timeout

**Implemented (this iteration):**

- `post_act_verify: true` — auto screenshot after successful act+verify → `.vdisplay/observe/{task-id}-post-verify.png`
- `preflight_actuation` — fail fast when vision actuation has no OCR and no map file
- `decision_data` in task feedback (action_ref, map/OCR readiness, data_locations)
- `bash examples/dev-workflow/setup-autonomy.sh` — vision deps + optional `--build-map`
- `bash examples/dev-workflow/run-dev-automation.sh --autonomy --setup-vision --reset`

### Cross-IDE smoke (JetBrains → Cursor)

Validates **koru + vdisplay** paths independently per IDE:

| IDE | vdisplay | koru |
|-----|----------|------|
| PyCharm (DP-2) | `ide prompt` + map | `autopilot drive --ide jetbrains` |
| Cursor (DP-1) | `control find` vision OCR | `autopilot drive --ide cursor` |

```bash
bash examples/dev-workflow/run-dev-automation.sh --cross-ide --reset
```

Planfile: [examples/dev-workflow/planfile-cross-ide.yaml](../../examples/dev-workflow/planfile-cross-ide.yaml). Planfile tasks may set `koru_instance: jetbrains|cursor` — auto runner scopes `KORU_AUTOPILOT_*` env.

### Faza 2 — Stan i replanning

- Persistent GUI maps per monitor (`map refresh --scope`)
- vision_llm for screenshot → action planning
- ScreenContext session dir (`.vdisplay/session/`)
- Keeper heartbeat + auto `--force` re-adopt

### Faza 3 — Self-dev via vdisplay

Develop vdisplay using vdisplay on the same PC:

```bash
bash examples/dev-workflow/run-dev-automation.sh          # capture regression
vdisplay app open cursor --variant default
vdisplay control find --backend vision --vision-anchor Ask --map maps/chat.json
vdisplay ide prompt --ide cursor --map maps/chat.json --text "add retry to atspi"
.venv/bin/pytest tests/test_screencast*.py -q
```

### Faza 4 — E2E + docs + safety

- E2E: observe DP-1 → launch Cursor → control chat → verify screenshot
- `auto --dry-run`, confirm via NLP, session audit in `.vdisplay/`

## Planfile task schema (autonomy)

```yaml
automation:
  - id: chat-cursor
    title: Type into Cursor chat with verify
    status: todo
    priority: high
    monitor: DP-1
    map: maps/chat.json
    verify: true
    observe: true
    handler: vdisplay ide prompt --ide cursor --target message --text "hello"
```

| Field | Purpose |
|-------|---------|
| `monitor` / `source` | Capture scope (`--source DP-1`, `VDISPLAY_CAPTURE_SOURCE`) |
| `map` | GUI map path (auto `--map` on control commands) |
| `verify: true` | Auto-append `--verify`; fail task if `verified: false` in JSON |
| `observe: true` | Preflight screenshot + ScreenContext before act |

## Success criteria

Full autonomy when this runs unattended on your 3-monitor setup:

```bash
vdisplay auto --planfile examples/dev-workflow/planfile-autonomy.yaml --source yaml run
# OR (future)
vdisplay nlp "otwórz Cursor, wpisz prompt, zweryfikuj screenshotem DP-1"
```

System must: screencast/observe → understand UI (NL/vision) → multi-step act → verify → recover from keeper/AT-SPI failures.

## Risks

| Risk | Mitigation |
|------|------------|
| Native Wayland apps invisible to AT-SPI | vision + map primary path |
| Flaky capture | keeper `--force`, probe per monitor |
| Slow observe | cache ScreenContext, scoped crops |
| Safety | dry-run, `.vdisplay` audit, confirm gates |
