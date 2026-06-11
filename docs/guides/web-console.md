# Guide: web console (multi-monitor control desk)

**Question:** How do I monitor and control the desktop host from a browser?

The **vdisplay web console** is served by `vdisplay-agent` at `/web`. It aggregates broker state (monitors, screencast, sampler, tasks, windows) and shows live PNG frames per monitor. Use it to supervise automation, start/stop capture, and (MVP) queue replay of `.vdisplay` audit sessions.

Back to [start-here.md](../start-here.md) · Full broker API: [agent-broker.md](../agent-broker.md)

## Prerequisites

```bash
pip install -e ".[pillow,dev]"
pip install -e "packages/vdisplay-agent[serve]"
```

On a **development checkout**, export `PYTHONPATH` so the agent loads local sources:

```bash
export PYTHONPATH=src:packages/vdisplay-agent/src
```

Optional Playwright tests:

```bash
pip install -e ".[e2e]"
python -m playwright install chromium
```

## Start the console

```bash
# terminal 1 — broker (localhost only)
export PYTHONPATH=src:packages/vdisplay-agent/src   # dev checkout only
vdisplay-agent serve
# default http://127.0.0.1:8765

# terminal 2 — open UI
xdg-open http://127.0.0.1:8765/web
```

Wayland host capture requires a persistent ScreenCast session **before** monitor tiles show real frames:

```bash
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
vdisplay agent screencast start    # portal picker — pick All Screens or monitor with IDE (e.g. DP-1)
```

Order matters: start the agent first, then screencast. See [agent-broker.md](agent-broker.md).

## Console panels

| Panel | Purpose |
|-------|---------|
| **Sterowanie** | Start/stop ScreenCast and Sampler; auto-refresh interval |
| **Monitors** | Live PNG tile per connected output — **click** sends pointer via ydotool/xdotool |
| **Odtwarzanie** | List `.vdisplay` audit sessions; queue replay (MVP) |
| **Ustawienia** | Refresh interval display; agent token hint |
| **Zadania** | Broker tasks (`/tasks`) |
| **Okna / aplikacje** | XWayland window list (native Wayland apps often missing) |

Status pills in the header reflect screencast readiness and sampler state.

## HTTP API (web-specific)

All routes accept optional `Authorization: Bearer $VDISPLAY_AGENT_TOKEN`.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/web` | HTML dashboard |
| GET | `/api/web/overview` | Monitors, screencast, sampler, tasks, windows, capabilities |
| GET | `/api/web/frame/{monitor_name}` | PNG for one monitor (short TTL cache) |
| GET | `/api/web/frames` | JSON list of all monitor frames |
| POST | `/api/web/screencast/start` | Start portal ScreenCast (`multiple: true` default) |
| POST | `/api/web/sampler/start` | Start background sampler (`all_monitors: true` default) |
| GET | `/api/web/replay/sessions` | List recorded sessions under `.vdisplay/` |
| POST | `/api/web/replay/start` | Start background replay (`{"session_id": "…"}`) |
| POST | `/api/web/pointer/click` | Click on monitor image (`monitor_name`, `x`, `y`, `coord_space=png`) |
| GET | `/api/web/replay/status/{job_id}` | Poll replay job status + report |

Quick checks:

```bash
curl -s http://127.0.0.1:8765/web | head -5
curl -s http://127.0.0.1:8765/api/web/overview | jq '.data | {monitors: .monitors.monitor_count, screencast: .screencast.active, sampler: .sampler.running}'
curl -s -o /tmp/DP-1.png -w "%{http_code}\n" http://127.0.0.1:8765/api/web/frame/DP-1
curl -s http://127.0.0.1:8765/api/web/replay/sessions | jq .
```

## Replay sessions

Recorded audit trails live under `~/.vdisplay/<session-id>/` (override root with `VDISPLAY_SESSION_BASE`).

Sources include `koru drive` steps and vdisplay CLI session recorder. The console lists sessions with step counts. **`POST /api/web/replay/start`** replays `CONTROL_CLICK`, `CONTROL_FOCUS`, and `CONTROL_SET_VALUE` steps in a background thread (delay: `VDISPLAY_REPLAY_DELAY_S`, default `0.25` s). Poll **`GET /api/web/replay/status/{job_id}`** for completion.

```bash
export VDISPLAY_SESSION=1
koru autopilot drive --ide jetbrains --direct --verify "test"   # writes audit under .vdisplay/
ls ~/.vdisplay/
```

## Testing

### Unit tests (mocked broker)

```bash
export PYTHONPATH=src:packages/vdisplay-agent/src
pytest tests/test_agent_web_console.py -q
```

### Playwright E2E (mock server)

Headless tests start an in-process agent with mocked overview/capture — no real ScreenCast required:

```bash
pytest tests/e2e/test_web_console_playwright.py -m e2e -v
```

### Playwright live (real agent)

Requires a running broker at `VDISPLAY_AGENT_URL` (default `http://127.0.0.1:8765`):

```bash
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
pytest tests/e2e/test_web_console_live.py -m live -v
```

Live tests read real monitors and frames; they do **not** click ScreenCast start (portal would block headless runs).

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `/web` → 404 | Agent too old or wrong package — reinstall `pip install -e packages/vdisplay-agent[serve]` and restart |
| Monitor tiles empty / capture 503 | Start ScreenCast: `vdisplay agent screencast start` |
| Replay panel shows API error | Restart agent after upgrade; check `GET /api/web/replay/sessions` |
| Stale UI after code change | Restart `vdisplay-agent serve`; HTML is read from disk on each request |
| Native Wayland apps missing in Okna | Expected — list is XWayland; use vision/map for PyCharm. See [wayland-control.md](wayland-control.md) |
| `Authorization` failures | Set matching `VDISPLAY_AGENT_TOKEN` on agent and in browser `localStorage.vdisplay_agent_token` |

More: [troubleshooting.md](../troubleshooting.md#web-console)

## Related

- [agent-broker.md](../agent-broker.md) — full HTTP API
- [session-report.md](session-report.md) — session recorder / audit trail
- [wayland-control.md](wayland-control.md) — PyCharm / multi-monitor capture
- [desktop-control-today.md](desktop-control-today.md) — current capabilities and gaps
