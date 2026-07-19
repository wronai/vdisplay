# STARTER-002: Replace starter tickets with your real backlog

model: qwen/qwen3-coder-next

## Prompt

Edit `.planfile/sprints/current.yaml` and add the work that
actually matters for this project. You can also re-run
`koru --init --force --from your-pipeline.yaml` to import a
flat pipeline you already maintain elsewhere.

---
Deliverable: a concrete, ordered action plan with exact shell commands and file paths where applicable, short enough to execute directly. State assumptions explicitly; do not pad.

## Answer

**Assumptions**  
1. `.planfile/sprints/current.yaml` exists and is valid YAML (if not, create it).  
2. You have an existing pipeline in `your-pipeline.yaml` (replace with actual path if different).  
3. “Work that matters” = high-impact, well-defined, executable tasks—no vague items.  
4. Project uses `koru` CLI (from `@koru/planner`) for sprint bootstrapping.

---

### ✅ Immediate Action Plan (≤ 5 minutes)

#### Step 1: If you have an existing pipeline elsewhere, import it:
```bash
koru --init --force --from your-pipeline.yaml
```
→ *This overwrites `.planfile/sprints/current.yaml` with the flat pipeline.*

#### Step 2: If no pipeline exists, create a minimal but concrete `current.yaml`:
```bash
cat > .planfile/sprints/current.yaml << 'EOF'
name: current
start: $(date +%Y-%m-%d)
end: $(date -v+14d +%Y-%m-%d)  # 2-week sprint
tasks:
  - id: m1
    title: "Setup core data pipeline"
    type: infra
    effort: 2
    depends_on: []
    cmd: |
      mkdir -p src/pipeline
      touch src/pipeline/engine.py src/pipeline/loader.py
      echo 'def run(): pass' > src/pipeline/engine.py
  - id: m2
    title: "Integrate OAuth provider"
    type: feature
    effort: 3
    depends_on: ["m1"]
    cmd: |
      pip install authlib
      curl -s https://raw.githubusercontent.com/org/secrets/main.yaml -o .env.local
  - id: m3
    title: "Write first E2E test"
    type: quality
    effort: 2
    depends_on: ["m2"]
    cmd: |
      pytest tests/e2e/test_login.py --create-db
EOF
```
*(Shell vars like `$(date)` expand at `cat` time; adjust dates as needed.)*

#### Step 3: Validate & run:
```bash
koru sprint validate .planfile/sprints/current.yaml
koru sprint start
```

---

> 🔑 **Critical note**: Skip vague tasks like "Review docs" or "Planning". Only add tasks that:  
> - Have a *single, executable command* or script in `cmd`  
> - Are prioritized *in order of impact/risk*  
> - Depend explicitly on prior deliverables (`depends_on`)
