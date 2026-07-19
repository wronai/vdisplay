# STARTER-008: Bootstrap wup on-change gate

model: qwen/qwen3-coder-next

## Prompt

`wup` is installed but no `wup.yaml` config exists in the project root. Bootstrap with `task template:install:wup` (in koru) or follow `workflows/on-change-gates.md`.

Role: intelligent file watcher (3-layer: detect → quick → full).

---
Deliverable: a concrete, ordered action plan with exact shell commands and file paths where applicable, short enough to execute directly. State assumptions explicitly; do not pad.

## Answer

**Assumptions**  
1. You are in the project root (where `wup` expects `wup.yaml`).  
2. `koru` CLI is installed and `task` is available (e.g., via `taskfile` or `just`).  
3. You want to bootstrap `wup.yaml` using the `koru` task.  
4. No `wup.yaml` currently exists (confirmed via `ls wup.yaml` fails).  

---

### Action Plan (≤ 3 commands)

1. **Verify `wup` is installed and `wup.yaml` is missing**  
   ```bash
   wup --version && [ ! -f wup.yaml ] && echo "OK: Proceed" || echo "FAIL: wup.yaml exists or wup missing"
   ```

2. **Bootstrap `wup.yaml` using `koru` task**  
   ```bash
   task template:install:wup
   ```

3. **Verify `wup.yaml` was created**  
   ```bash
   test -f wup.yaml && echo "SUCCESS: wup.yaml created" || echo "ERROR: wup.yaml not found"
   ```

---

**If step 2 fails** (e.g., `task` not found or task missing):  
→ Follow `workflows/on-change-gates.md` manually:  
```bash
cp .koru/templates/wup.yaml.example wup.yaml  # or equivalent path in your repo
```  
*(Adjust path if `.koru` is elsewhere; default assumes `koru` stores templates in `.koru/templates/`.)*
