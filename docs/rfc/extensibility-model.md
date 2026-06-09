# Extensibility model (index)

Status: **accepted** — see [RFC 001](./001-extensibility-model.md) for the canonical specification.

## Quick reference

| Concept | Module |
|---------|--------|
| Selector environment | `EnvironmentKind` — `control/models.py` |
| Host environment | `HostEnvironmentKind` on `PlatformProfile` — `control/descriptors.py` |
| Session lifecycle | `SessionKind` — `control/session_kind.py` |
| App class | `ApplicationProfile` — `control/descriptors.py` |
| Adapter metadata | `ProviderDescriptor` — `control/descriptors.py` |
| Plugin registration | `control/plugins.py` |
| Routing | `scoring.py` + `router.py` + `profile_inference.py` |
| Verify | `verify_strategy.py` + `verifier.py` |

## PR status

| PR | Scope | Status |
|----|-------|--------|
| PR-4 … PR-21 | Extension model + cross-platform UIA/AX invoke + vision OCR | **done** |
| PR-22+ | See [RFC 001 — Recommended next PRs](./001-extensibility-model.md#recommended-next-prs) | planned |

## Diagnostics

- `vdisplay diagnose control` / `GET /diagnostics/control`
- `GET /control/plugins`
- `GET /sessions`
- `GET /tasks`

Details: [control-plane.md](../control-plane.md) · [agent-broker.md](../agent-broker.md)
