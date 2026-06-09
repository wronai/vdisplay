# RFC 001: Generic Control Extension Model for vdisplay

| Field | Value |
|-------|-------|
| Status | **Accepted** — phases 1–5 implemented (PR-4 … PR-13) |
| Authors | vdisplay contributors |
| Created | 2026-06-09 |
| Related | [control-plane.md](../control-plane.md) · [extensibility-model.md](./extensibility-model.md) |

## Goal

Make vdisplay open to new platforms, applications, and browser-specific APIs **without changing core routing logic** every time a new backend appears.

## Problem

The project supports multiple control and capture paths (AT-SPI, Playwright, terminal PTY, X11, vision fallback), but without a formal extension model each new surface risks scattering platform logic across core modules, provider implementations, and session code.

**RFC 001 freezes the contract:** core knows *what* to do and *which capabilities* are needed; adapters know *how* to do it.

## Proposed model

Provider-centric architecture with five layers:

```
Selector (core + extensions)
        ↓
Policy / routing (scoring + profile inference + router)
        ↓
Provider adapter (ControlProvider + ProviderDescriptor)
        ↓
Session adapter (SessionKind + session catalog)
        ↓
Verify strategy (VerifierPipeline)
```

Core must never branch on `if provider == "chrome"` or `if app == "firefox"`. Those are **application profiles** on shared **provider adapters**.

## Core types

### EnvironmentKind (two levels — do not conflate)

| Level | Type in code | Examples | Used for |
|-------|--------------|----------|----------|
| **Host / execution** | `HostEnvironmentKind` on `PlatformProfile` (`display_stack` retained) | `linux_x11`, `linux_wayland`, `linux_headless` | Capability probes, deps, policy |
| **Selector / target** | `EnvironmentKind` in `control/models.py` | `desktop`, `browser`, `terminal`, `vision` | Provider routing from selector |

RFC drafts used one name for both; implementation splits them deliberately. Host context is detected in `detect_platform_profile()` (`control/descriptors.py`).

### SessionKind

Describes lifecycle and ownership of a broker connection.

| RFC example | Implemented value | Module |
|-------------|-------------------|--------|
| `virtual_display` | `virtual` | `control/session_kind.py` |
| `mirror` | `mirror` | |
| `relay` | `relay` | |
| `browser` | `browser` | |
| `terminal` | `terminal` | |
| `screencast` | `screencast` | |
| — | `capture_sampler` | sampler worker |
| `control` | *planned* | ephemeral control-plane lease |

Unified catalog: `SessionMetadata` in `control/session.py`; APIs: `GET /sessions`, `GET /tasks`.

### ApplicationProfile

Describes a **class of app**, not a concrete instance.

| Field (RFC) | Implemented | Notes |
|-------------|-------------|-------|
| `kind` | `kind` | e.g. `browser`, `terminal`, `desktop_native` |
| `vendor` | `vendor` | optional; Chrome/Firefox are vendors, not providers |
| `preferred_providers` | `preferred_providers` | ranking boost, not hard routing |
| `selector_extensions` | `selector_extensions` | names of `SelectorExtension` entries |
| `verify_modes` | `verify_strategies` | string list aligned with `VerifyStrategy` |
| `known_constraints` | `notes` | human-readable constraints |

Builtin profiles: `web_spa`, `terminal_pty`, `native_gtk`, `electron_desktop`, `vision_only_surface`.

Inference: `profile_inference.py` — signals from selector fields (`dom_css`, `terminal_line`, `app`, …).

### ProviderDescriptor

Describes a concrete adapter and its capabilities.

| Field (RFC) | Implemented | Module |
|-------------|-------------|--------|
| `provider_id` | `provider_id` | `control/descriptors.py` |
| `supported_environments` | `environments` | frozenset of selector environments |
| `required_dependencies` | `required_deps` | probe strings |
| `session_kinds` | `session_kind` | single primary `SessionKind` per provider |
| `actions` | `actions` | frozenset |
| `selector_fields` | `selector_extensions` | per-provider extension tuples |
| `verify_modes` | `verify_strategies` | frozenset of `VerifyStrategy` |
| `priority` | `base_score` | scoring input |
| `confidence` | `cost` / `risk` | ranking penalties |

Registration: `ProviderRegistry` + `register_control_provider()` (`control/registry.py`, `control/plugins.py`).

### VerifyStrategy

| RFC example | Implemented | Status |
|-------------|-------------|--------|
| `structure` | `structure` | a11y tree diff |
| `text` | `text` | terminal / label text |
| `dom` | `dom` | browser snapshot diff |
| `screenshot` | `screenshot` | visual verify |
| `a11y` | *via* `structure` + AT-SPI | semantic path |
| `none` | `none` | skip verify |
| — | `hybrid`, `ocr` | production extras |

Pipeline: `control/verifier.py` — semantic, visual, OCR rescue; browser defaults to `dom` mode.

## Routing rules

Routing is **capability-driven**, **environment-aware**, and **explainable**.

Selection flow (implemented in `scoring.py` + `router.py`):

1. Build context from platform (`PlatformProfile`), selector, session hints, and optional `session_id`.
2. Infer `ApplicationProfile` (`profile_inference.py`).
3. Load registered providers (`ProviderRegistry` + plugins).
4. Filter/score by environment, readiness probes, session gates (`_terminal_session_ready`, `_browser_session_ready`).
5. Pick action provider and optional verify provider (`select_verify_provider`).
6. Return `ProviderRoutingDecision` with `why_selected`, `why_not_selected`, candidates.

Surfaces: `diagnose control`, `GET /diagnostics/control` — includes `routing`, `extensions`, `application_profile`.

## Plugin contract

Every `ControlProvider` implements:

| # | Method | Required |
|---|--------|----------|
| 1 | `available()` | yes |
| 2 | `snapshot()` | yes |
| 3 | `find()` | yes |
| 4 | `invoke()` | yes |
| 5 | `focus()` | yes |
| 6 | `set_value()` | yes |
| 7 | `bounds()` | yes |
| 8 | `capabilities()` | yes (descriptor default on `base.py`) |
| 9 | `verify_modes()` | yes (descriptor default) |
| 10 | `session_kind()` | yes (descriptor default) |

Register at runtime:

```python
from vdisplay.control import register_control_provider, ProviderDescriptor

register_control_provider(descriptor, factory)
```

Entry points: `[project.entry-points."vdisplay.control_providers"]` — see [control-plane.md](../control-plane.md).

## Application classes

Treat specific apps as **profiles**, not special backends.

| Class | Profile examples | Provider chain |
|-------|------------------|----------------|
| Browsers | Chrome, Firefox, Edge, Brave → `web_spa` + `vendor` | `browser` → `x11` |
| Terminals | GNOME Terminal, Alacritty, kitty, tmux, ssh → `terminal_pty` | `terminal` |
| Native desktop | GTK, Qt, Electron, LibreOffice → `native_gtk` / `electron_desktop` | `atspi` → `browser` → `x11` |
| Vision-only | games, canvas, streams → `vision_only_surface` | `x11` (screenshot/OCR) |

## Fallback chains

| Surface | Primary | Fallback | Verify |
|---------|---------|----------|--------|
| Browser | DOM / Playwright | X11 pointer | `dom`, `screenshot`, `hybrid` |
| Native desktop | AT-SPI | X11 → vision | `structure`, `screenshot`, `hybrid` |
| Terminal | PTY session | screen buffer | `text`, `structure` |

Session gates: browser and terminal providers require an open session (`browser_open`, `terminal_open`, agent routes) before they are eligible.

## File layout

| RFC module | Path | Status |
|------------|------|--------|
| models | `src/vdisplay/control/models.py` | done |
| base | `src/vdisplay/control/base.py` | done |
| policy | `src/vdisplay/control/policy.py` | done |
| selector | `src/vdisplay/control/selector.py` | done |
| engine | `src/vdisplay/control/engine.py` | done |
| registry | `src/vdisplay/control/registry.py` | done |
| plugins | `src/vdisplay/control/plugins.py` | done |
| profile inference | `src/vdisplay/control/profile_inference.py` | done |
| providers | `src/vdisplay/control/providers/*` | done (atspi, browser, terminal, x11) |
| verifier | `src/vdisplay/control/verifier.py` | done |
| session catalog | `src/vdisplay/control/session.py` | done |
| descriptors | `src/vdisplay/control/descriptors.py` | done |
| contracts | `src/vdisplay/control/contracts.py` | done |
| agent control | `packages/vdisplay-agent/.../services/control.py` | done |
| agent sessions | `packages/vdisplay-agent/.../services/sessions.py` | done |
| agent tasks | `packages/vdisplay-agent/.../services/tasks.py` | done |

## Migration plan

### Phase 1 — Freeze core types and descriptors

**Done** (PR-8). `ProviderDescriptor`, `ApplicationProfile`, `PlatformProfile`, `VerifyStrategy`, `SessionKind`.

### Phase 2 — Registry + policy routing

**Done** (PR-4, PR-5). `ProviderRegistry`, `ControlRouter`, scoring, explainability.

### Phase 3 — Port providers to descriptor contract

**Done** (PR-3 scope + PR-13). AT-SPI, Playwright/browser, terminal, X11; plugin defaults on `ControlProvider`.

### Phase 4 — Profile inference

**Done** (PR-9). Selector-driven inference; ranking boosts from `ApplicationProfile`.

### Phase 5 — Expose in CLI, DSL, REST, agent

**Mostly done** (PR-6, PR-10, PR-11, PR-13).

| Surface | Status |
|---------|--------|
| Agent control routes | done |
| `GET /sessions`, `GET /tasks`, `GET /control/plugins` | done |
| `POST /session/terminal/open` | done |
| `POST /session/browser/open` | done |
| DSL `TERMINAL_OPEN` | done |
| DSL `BROWSER_OPEN` | done |
| REST/MCP parity for sessions | partial |

## Compatibility

- Legacy payloads (`ControlNode`, `ControlSnapshot`, agent envelope) unchanged.
- New fields are additive: `routing`, `extensions`, `plugins`, `application_profile`, `sessions`, `tasks`.
- Old callers keep working; `diagnose control` exposes both legacy `control` contract and extension catalog.

## Non-goals

- Rewriting every provider at once.
- Hard-coding app-specific logic into core.
- Making every backend support every action.
- Windows UIA / macOS AX (future phase).
- pluggy / dynamic hot-reload (entry points only for now).
- Per-vendor top-level providers (Chrome as provider id).

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| New provider without editing core routing | **met** — `register_control_provider()` |
| New app profile without provider internals change | **met** — `ApplicationProfile` + inference |
| Explainable routing decisions | **met** — `ProviderRoutingDecision` |
| AT-SPI, Playwright, Terminal, X11 still work | **met** — contract tests |
| Stable unattended path per environment class | **partial** — terminal/browser need session open; capture policy separate |

## Implemented PRs (reference)

| PR | Scope |
|----|-------|
| PR-4 | Policy engine v2 |
| PR-5 | Contracts + registry + router |
| PR-6 | DSL `terminal open` |
| PR-7 | VerifierPipeline |
| PR-8 | Extension descriptors + catalog |
| PR-9 | Application profile inference |
| PR-10 | Session model unification |
| PR-11 | Agent task persistence (SQLModel) |
| PR-12 | Plugin registration API |
| PR-13 | Browser production (session registry, DOM verify) |
| PR-14 | DSL `browser open` + schema |
| PR-15 | `HostEnvironmentKind` on `PlatformProfile` |
| PR-16 | Browser engine profiles (`browser_firefox`, `browser_chromium`) |
| PR-17 | Vision provider stub + `vision_only_surface` routing |

## Recommended next PRs

1. **PR-18** — Plugin author guide + example wheel in `examples/control-plugin/`.
2. **PR-19** — Windows UIA / macOS AX providers (cross-platform phase).
3. **PR-20** — Vision invoke/OCR implementation (beyond stub).

## One-line principle

**New platforms and apps ship as adapter + profile + descriptor — never as core conditionals.**
