# Control plugin example (PR-18)

Minimal **installable wheel** that registers a custom `ControlProvider` via the
`vdisplay.control_providers` entry-point group. Use it as a template for third-party
adapters without editing vdisplay core.

## Layout

```
examples/control-plugin/
├── README.md
├── pyproject.toml
└── src/vdisplay_example_plugin/
    ├── __init__.py      # register_plugin() entry point
    └── my_provider.py   # EchoControlProvider + ProviderDescriptor
```

## 1. Implement `ControlProvider`

Subclass `vdisplay.control.base.ControlProvider` and implement:

| Method | Purpose |
|--------|---------|
| `available()` | Readiness probe `(ok, reason)` |
| `snapshot()` | Build `ControlSnapshot` tree |
| `find(selector)` | Match `ControlSelector` → `ControlNode` list |
| `invoke()` / `focus()` / `set_value()` | Actions |
| `bounds()` | Pixel bounds for an element |

See [`my_provider.py`](src/vdisplay_example_plugin/my_provider.py) — `EchoControlProvider`
returns a synthetic `demo-button` node for CI and integration tests.

## 2. Declare `ProviderDescriptor`

Metadata drives routing scores, capability contracts, and `diagnose control` output.
Do **not** add a new top-level provider per browser vendor — use `ApplicationProfile`
(see PR-16 `browser_firefox` / `browser_chromium`).

```python
ECHO_DESCRIPTOR = ProviderDescriptor(
    provider_id="echo",
    adapter_kind="example_echo",
    environments=frozenset({"desktop"}),
    session_kind=None,          # or SessionKind.BROWSER / TERMINAL
    capabilities=ECHO_CAPABILITIES,
    base_score=35,
    aliases=frozenset({"example-echo"}),
)
```

## 3. Register — three ways

### A. Entry point (recommended for wheels)

`pyproject.toml`:

```toml
[project.entry-points."vdisplay.control_providers"]
echo = "vdisplay_example_plugin:register_plugin"
```

`register_plugin()` calls `register_control_provider(descriptor, factory, source="entrypoint")`.
vdisplay loads entry points on first `get_provider_registry()` call.

### B. Runtime (tests, host integrations)

```python
from vdisplay.control.plugins import register_control_provider
from vdisplay_example_plugin import ECHO_DESCRIPTOR, EchoControlProvider

register_control_provider(
    ECHO_DESCRIPTOR,
    lambda **kwargs: EchoControlProvider(**kwargs),
    source="manual",
)
```

### C. Builtin (vdisplay core only)

Core builtins live in `src/vdisplay/control/providers/` and
`BUILTIN_PROVIDER_DESCRIPTORS` — avoid for third-party code.

## 4. Application profiles (optional)

Profiles describe **app class**, not execution adapter. Add to
`BUILTIN_APPLICATION_PROFILES` only when upstreaming a generic class (e.g. `web_spa`).
Third-party profiles can be inferred via plugin-specific selector fields or
`register_control_provider` + custom scoring in a future PR.

For browser targets, use **engine profiles** (`browser_chromium`, `browser_firefox`) —
the `browser` provider stays the executor.

## 5. Install and verify

```bash
cd ~/github/wronai/vdisplay
source venv/bin/activate
pip install -e ".[dev]"
pip install -e examples/control-plugin

# Plugin visible in diagnostics
vdisplay diagnose control | jq '.extensions.plugins[] | select(.provider_id=="echo")'

# Agent broker
vdisplay agent serve &
curl -s http://127.0.0.1:8765/control/plugins | jq '.data.plugins[] | select(.provider_id=="echo")'
```

## 6. Tests

Main suite includes `tests/test_example_control_plugin.py` (manual registration)
and contract tests ensuring **builtin provider count stays 5** when no plugin is loaded.

```bash
pytest tests/test_example_control_plugin.py tests/test_control_plugins.py -q
pytest tests/contract/test_providers.py -q   # builtin count unchanged
```

## 7. Checklist for plugin authors

- [ ] `ProviderDescriptor.provider_id` is unique and lowercase
- [ ] `capabilities` match what `invoke`/`find` actually support
- [ ] `session_kind` set if provider requires `browser_open` / `terminal_open`
- [ ] `base_score` lower than primary builtins unless you intend to win auto-routing
- [ ] Entry point or `register_control_provider` — never patch `scoring.py`
- [ ] Tests: `available()`, `find()`, routing eligibility, unregister cleanup

## References

- RFC: [`docs/rfc/001-extensibility-model.md`](../../docs/rfc/001-extensibility-model.md)
- Plugin API: `src/vdisplay/control/plugins.py`
- Contract tests: `tests/contract/test_providers.py`
- PR-12 tests: `tests/test_control_plugins.py`
