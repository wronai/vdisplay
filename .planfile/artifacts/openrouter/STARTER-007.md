# STARTER-007: Bootstrap regix on-change gate

model: qwen/qwen3-coder-next

## Prompt

`regix` is installed but no `regix.yaml` config exists in the project root. Bootstrap with `task template:install:regix` (in koru) or follow `workflows/on-change-gates.md`.

Role: regression metrics gate (CC / MI / coverage delta).

---
Deliverable: a concrete, ordered action plan with exact shell commands and file paths where applicable, short enough to execute directly. State assumptions explicitly; do not pad.

## Answer

**Assumptions**  
- You are in the project root (where `regix` is installed).  
- `task` (go-task) is available and `koru` taskfile exists.  
- `workflows/on-change-gates.md` is accessible locally (e.g., at `.github/workflows/on-change-gates.md`).  
- You have write access to create `regix.yaml` in the project root.

---

**Action Plan**

1. **Bootstrap `regix.yaml` using `task` (preferred)**  
   ```bash
   task template:install:regix
   ```

2. **If step 1 fails (e.g., no `koru` taskfile), manually create `regix.yaml`**  
   ```bash
   cat > regix.yaml <<'EOF'
   version: "1"
   metrics:
     - name: coverage_delta
       type: coverage
       threshold: -5  # allow up to 5% drop
     - name: cc
       type: complexity
       threshold: 10  # max cyclomatic complexity per function
     - name: mi
       type: maintainability
       threshold: 65  # min maintainability index
   paths:
     - "./..."
   exclude:
     - "**/*_test.go"
     - "vendor/**"
   EOF
   ```

3. **Verify config**  
   ```bash
   regix check
   ```

Done.
