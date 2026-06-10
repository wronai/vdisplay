# Windows UIA control plugin example (PR-23)

Installable wheel that registers an **`example-uia`** provider via the
`vdisplay.control_providers` entry-point group. It wraps the core
`UiaControlProvider` and shows how to ship **Windows-only semantic control**
as an optional package with platform deps (`comtypes`).

On non-Windows hosts (CI, Linux dev machines) the plugin uses
`MockUiaBackend` with a synthetic Notepad tree so tests and docs run everywhere.

## Layout

```
examples/control-plugin-uia/
├── README.md
├── pyproject.toml
└── src/vdisplay_example_uia_plugin/
    ├── __init__.py      # register_plugin() entry point
    └── provider.py      # ExampleUiaProvider + ProviderDescriptor
```

## Install

```bash
cd ~/github/wronai/vdisplay
source venv/bin/activate
pip install -e ".[dev]"
pip install -e examples/control-plugin-uia

# Windows native UIA (optional)
pip install -e "examples/control-plugin-uia[windows]"
export VDISPLAY_UIA_MOCK=0   # use comtypes + UIAutomationCore on win32
```

## Verify registration

```bash
vdisplay diagnose control | jq '.extensions.plugins[] | select(.provider_id=="example-uia")'

# Forced routing (mock tree on Linux)
vdisplay control list --backend example-uia --app Notepad
vdisplay control click --backend example-uia --role button --name Save --verify
```

## Mock vs native

| Host | Default backend | Override |
|------|-----------------|----------|
| Linux / CI | `MockUiaBackend` (Notepad demo tree) | `VDISPLAY_UIA_MOCK=1` |
| Windows | Native `ComtypesUiaBackend` | `VDISPLAY_UIA_MOCK=1` forces mock |
| Windows (native) | comtypes UIA | `VDISPLAY_UIA_MOCK=0` |

## Production pattern

vdisplay core already ships builtin `uia` with host-gated scoring. For a
**third-party or OEM wheel**, reuse this layout but:

1. Set `provider_id="uia"` (or your vendor id) in `ProviderDescriptor`
2. Declare `comtypes` in `[project.dependencies]` with `sys_platform == 'win32'` marker
3. Keep invoke/find logic in the wheel — do **not** patch `scoring.py`
4. Add an `ApplicationProfile` only when targeting a class of apps, not a platform

See also: [control-plugin-ax](../control-plugin-ax/) (macOS), [control-plugin](../control-plugin/) (minimal echo stub).

## Tests

```bash
pytest tests/test_example_uia_ax_plugins.py -q
```

## References

- RFC: [`docs/rfc/001-extensibility-model.md`](../../docs/rfc/001-extensibility-model.md)
- Core UIA: `src/vdisplay/control/providers/uia.py`
- Plugin API: `src/vdisplay/control/plugins.py`
