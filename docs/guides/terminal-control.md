# Guide: terminal control

**Question:** How do I automate a PTY terminal session?

## Open session

```bash
dsl2vdisplay -c 'TERMINAL_OPEN SESSION_ID t1 COMMAND bash ROWS 24 COLS 80'
# or
vdisplay agent terminal open --session-id t1 --command bash   # via broker API
```

## Grid selectors

```bash
vdisplay control set-value --backend terminal --session-id t1 \
  --terminal-line 1 --value "echo hello" --verify

vdisplay control find --backend terminal --session-id t1 --text-contains "hello"
```

## Routing

Terminal provider activates when `terminal_line`, `terminal_col`, or terminal `session_id` is set.

Full control plane reference: [control-plane.md](../control-plane.md)

Example: [examples/control-plane/](../../examples/control-plane/)
