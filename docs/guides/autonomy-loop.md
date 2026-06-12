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

**Koru photo-VQL drives (2026-06-12+):** each run is scoped to a **date folder**:

```
.vdisplay/
  YYYY-MM-DD/
    YYYY-MM-DDTHH-MM-SSZ__koru-{ide}/
      session.json          # manifest (ide, source, max_age)
      index.jsonl             # observe → decide → act timeline
      observe/
        prepare.json          # prepare_photo_vql_for_drive output
        capture.png           # fresh screenshot (only source for decide)
        capture.png.vql.json
      decide/
        vql_target.json       # VQL target + llm_decision
        stale_abort.json      # when sidecar too old / mismatch
      act/
        drive_result.json     # focus + edit + coords + llm_used
      verify/                 # post-paste checks (future)
```

Stale global files (`.vdisplay/koru-cont-dp*.png` older than `KORU_VDISPLAY_VQL_MAX_AGE_S`, analysis JSONs, IMGL sidecars older than PNG) are **ignored** by `load_vql_metadata()` — decide/act never reads them during an active session.

**Reset** (delete sessions, captures, broker log; recreates empty layout):

```bash
vdisplay config --project . clear
vdisplay config --project . clear --dry-run
```

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

## Koru photo-VQL decision loop (step-by-step)

Used by `koru-drive-photo-vql.sh`, `prepare_photo_vql_for_drive()`, `send_chat()` with `KORU_VDISPLAY_LLM_VISION_DECISION=1`.

| Step | Function | Input | Output in session |
|------|----------|-------|-------------------|
| 1. **Session** | `begin_autonomy_session()` | ide, source | `.vdisplay/YYYY-MM-DD/ISO__koru-{ide}/` |
| 2. **Observe** | `prepare_photo_vql_for_drive` → `ensure_vdisplay_ide_control` + `refresh_photo_vql_sidecar` | live screenshot | `observe/prepare.json`, `observe/capture.png` + `.vql.json` |
| 3. **Freshness gate** | `load_vql_metadata()` / `vql_sidecar_is_stale()` | max age (default 300s) | skip stale; abort if session active |
| 4. **IDE match** | `_photo_vql_ide_window_warning()` | **window title layer only** | `ide_window_warning` if Cursor≠PyCharm |
| 5. **Decide** | `get_vql_chat_target_from_photo` + `_resolve_photo_vql_llm_coords` | PNG + VQL + OpenRouter | `decide/vql_target.json` |
| 6. **Act** | `move_mouse_to_vql_target_and_focus_keyboard` + `_type_text_at_vql_coords` | refined x,y | `act/drive_result.json` |
| 7. **Audit** | `record_koru_drive_step` | full payload | vdisplay session steps + `index.jsonl` |

### Cursor positioning logs (chat write failures)

When typing misses the chat composer, inspect (in order):

1. `.vdisplay/YYYY-MM-DD/*/decide/vql_chat_candidates.json` — all VQL input layers scored
2. `.vdisplay/YYYY-MM-DD/*/decide/vql_chat_target_selected.json` — chosen target + `warnings`
3. `.vdisplay/YYYY-MM-DD/*/act/cursor_positioning.jsonl` — **exact local/global coords at each command stage**
4. `.vdisplay/YYYY-MM-DD/*/act/command_plan_*.json` — generated `POINTER_MOVE` / `CLIPBOARD_PASTE` sequence from VQL
5. `drive_reply.vql_command_plan.warnings` — e.g. `chat_local_y=799_below_850` means editor not chat

Logger keys (grep): `VQL_CHAT_TARGET_CANDIDATES`, `VQL_CURSOR_POSITIONING`, `VQL_CURSOR_POSITIONING_SUSPICIOUS`, `VQL_YDOTOOL_COMMAND_MAPPED`, `VQL_CHAT_WRITE_PASTE_OK`.

### Capture guards (JetBrains / Wayland)

- `capture_confirmed` comes from **window title layer**, not map actuation success.
- `body_false_positive: true` when OCR sees IDE name in document body (e.g. Cursor) but not in titlebar.
- **Terminal pollution:** when the control terminal running `bash koru-drive-*.sh` is on the captured monitor (DP-2), imgl OCR reads bash history as "button/input" VQL candidates. Guard: `_VQL_TERMINAL_LABEL_NOISE` (20+ tokens: `KORU_`, `DRY_RUN`, `PREFER`, `po clear`, `recznie`, `wpisz`, `audit`, etc.) → heavy score penalty (-1500) → reject candidates with shell/command/env tokens. Pollution also triggers `ide_window_mismatch` + `capture_confirmed: false`.
- Default: drive **aborts** if foreground ≠ PyCharm; set `KORU_VDISPLAY_ALLOW_MAP_ON_MISMATCH=1` only for controlled tests.
- Full checklist: `semcod/koru/docs/photo-vql-jetbrains-wayland.md`.

### Guard env vars (JetBrains / Wayland)

| Variable | Default | Meaning |
|----------|--------|---------|
| `KORU_VDISPLAY_RAISE_ALT_TAB` | auto on for JetBrains | Alt+Tab focus recovery before abort |
| `KORU_VDISPLAY_ALLOW_MAP_ON_MISMATCH` | off | Map-only path when capture title ≠ target IDE (test/escape hatch) |
| `KORU_VDISPLAY_ALLOW_IDE_MISMATCH` | off | Broader guard bypass for actuation |
| `KORU_VDISPLAY_VERIFY_AFTER_PASTE` | on | OCR verify after paste; `ok: false` when text not visible |
| `KORU_VDISPLAY_DRY_RUN` | off | Dry-run mode (no actual paste/ydotool) |
| `VDISPLAY_CAPTURE_VALIDATE_IDE` | `jetbrains` in drive script | Pre-check window title on screenshot |
| `KORU_VDISPLAY_VQL_MAX_AGE_S` | `300` | Sidecars older than this are not used for decide |
| `KORU_VDISPLAY_PHOTO_VQL_REFRESH` | `auto` | `auto` = refresh when missing/stale/mismatch; `always` = every run |
| `VDISPLAY_SESSION` | `1` in drive script | Enables `record_koru_drive_step` audit |

### Audit

```bash
bash examples/dev-workflow/koru-audit-last-session.sh --ide jetbrains
```

Section **0. Prepare/observe** reads `observe/prepare.json` (`capture_confirmed`, `competing_ide`, `focus_recovery`, `visual_guard_failed`).

### Entry command (JetBrains DP-2)

```bash
export KORU_VDISPLAY_LLM_VISION_DECISION=1
export KORU_VDISPLAY_PREFER_PHOTO_VQL=1
export KORU_VDISPLAY_SOURCE=DP-2
export KORU_VDISPLAY_VQL_MAX_AGE_S=300
bash examples/dev-workflow/koru-drive-photo-vql.sh \
  --ide jetbrains --source DP-2 --prompt "twoje polecenie"
# Inspect: .vdisplay/$(date +%Y-%m-%d)/*/act/drive_result.json
```

## Risks

| Risk | Mitigation |
|------|------------|
| Native Wayland apps invisible to AT-SPI | vision + map primary path |
| Flaky capture | keeper `--force`, probe per monitor |
| Slow observe | cache ScreenContext, scoped crops |
| Safety | dry-run, `.vdisplay` audit, confirm gates |
