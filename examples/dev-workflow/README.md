# Dev workflow — develop vdisplay using vdisplay on this PC

Automated smoke test for the **GNOME Wayland 3-monitor** setup (DP-1, DP-2, HDMI-1).

## Koru + vdisplay — pętla autonomiczna (photo-VQL)

**Cel:** wpisać prompt do czatu IDE (PyCharm, Cursor, …) przez **observe → decide → act → verify**, bez fałszywego `ok: true` gdy zrzut ekranu pokazuje inne okno.

Koru orkiestruje; vdisplay robi capture, VQL (imgl), map/ydotool i audit w `.vdisplay/`.

```
observe (prepare + screenshot + VQL)
    → decide (target chat / LLM vision)
    → act (mouse + paste + submit)
    → verify (OCR po wklejce)
```

Artefakty sesji: `.vdisplay/YYYY-MM-DD/ISO__koru-{ide}/` — `observe/prepare.json`, `decide/*`, `act/drive_result.json`.

| Dokument | Opis |
|----------|------|
| [docs/guides/autonomy-loop.md](../../docs/guides/autonomy-loop.md) | Layout sesji, env, guardy |
| [semcod/koru/docs/photo-vql-jetbrains-wayland.md](https://github.com/semcod/koru/blob/main/docs/photo-vql-jetbrains-wayland.md) | PyCharm/Wayland/DP-2, checklista, troubleshooting |

### Wymagania

```bash
cd ~/github/wronai/vdisplay
source .venv/bin/activate
pip install -e ".[observe,pillow,dev,auto]" -e "packages/vdisplay-agent[serve]"

# repozytoria obok siebie (ścieżki domyślne w skryptach):
#   ~/github/semcod/koru/src
#   ~/github/semcod/imgl

# system: tesseract-ocr, ydotool (Wayland), opcjonalnie xdotool (XWayland)
bash examples/dev-workflow/setup-autonomy.sh
```

**Terminal 1 — broker (ta sama sesja GNOME):**

```bash
export PYTHONPATH=src:packages/vdisplay-agent/src
vdisplay-agent serve
# lub: vdisplay agent screencast start --force
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
```

**OpenRouter (opcjonalnie, LLM refine coords z foto):** klucz w `vdisplay/.env` lub `export OPENROUTER_API_KEY=...` — skrypt `koru-drive-photo-vql.sh` ładuje go automatycznie.

### Szybki start — jeden drive (PyCharm)

```bash
cd ~/github/wronai/vdisplay
source .venv/bin/activate

# 1. Monitory
vdisplay monitors
# JetBrains na DP-2: --source DP-2  |  Cursor na DP-1: --source DP-1

# 2. Pre-check — tytuł okna musi pasować do IDE (nie Cursor gdy target=jetbrains)
VDISPLAY_CAPTURE_VALIDATE_IDE=jetbrains \
  vdisplay screenshot --source DP-2 | jq '.capture_validation // empty'

# 3. Przed drive: PyCharm na wierzchu na tym monitorze, terminal poza kadrem zrzutu

# 4. Real drive (wpis + submit)
unset KORU_VDISPLAY_DRY_RUN
KORU_SRC=~/github/semcod/koru/src IMGL_SRC=~/github/semcod/imgl \
  bash examples/dev-workflow/koru-drive-photo-vql.sh \
  --ide jetbrains --source DP-2 --prompt "twoje polecenie" --submit

# 5. Audit ostatniej sesji
bash examples/dev-workflow/koru-audit-last-session.sh --ide jetbrains
```

**Dry-run** (tylko prepare + plan, bez paste):

```bash
KORU_VDISPLAY_DRY_RUN=1 bash examples/dev-workflow/koru-drive-photo-vql.sh \
  --ide jetbrains --source DP-2 --prompt "test"
```

### Skrypty entrypoint

| Skrypt | Rola |
|--------|------|
| `koru-drive-photo-vql.sh` | Pełna pętla: `prepare_photo_vql_for_drive` → `send_chat` |
| `koru-audit-last-session.sh` | Podsumowanie sesji (prepare, decide, act) |
| `run-dev-automation.sh --autonomy` | Planfile vdisplay (observe/find/act bez koru chat) |

### Ważne zmienne środowiskowe

| Zmienna | Domyślnie | Znaczenie |
|---------|-----------|-----------|
| `KORU_SRC` | `~/github/semcod/koru/src` | Moduł `koru.integrations.vdisplay_client` |
| `IMGL_SRC` | `~/github/semcod/imgl` | **Musi być przed `KORU_SRC` w PYTHONPATH** (stub `koru/src/imgl` inaczej daje 0 warstw VQL) |
| `KORU_VDISPLAY_SOURCE` | auto / z `--source` | Monitor capture (`DP-1`, `DP-2`, …) |
| `VDISPLAY_CAPTURE_VALIDATE_IDE` | `jetbrains` w drive script | Walidacja tytułu okna na zrzucie |
| `KORU_VDISPLAY_VQL_MAX_AGE_S` | `300` | Sidecar VQL starszy niż to — ignorowany |
| `KORU_VDISPLAY_LLM_VISION_DECISION` | `1` w drive script | OpenRouter refine współrzędnych chat |
| `KORU_VDISPLAY_RAISE_ALT_TAB` | auto **on** dla JetBrains | Alt+Tab recovery przed abortem prepare |
| `KORU_VDISPLAY_ALLOW_MAP_ON_MISMATCH` | off | Map-only mimo złego tytułu — **tylko testy** |

Pełna lista: [autonomy-loop.md](../../docs/guides/autonomy-loop.md) · [photo-vql-jetbrains-wayland.md](https://github.com/semcod/koru/blob/main/docs/photo-vql-jetbrains-wayland.md).

### Integracja z `koru autonomous`

W projekcie z `koru.yaml` / planfile, lane JetBrains może używać vdisplay fallback:

```bash
export KORU_VDISPLAY_CONTROL_FALLBACK=1
export KORU_VDISPLAY_USE_VQL_MOUSE_FOCUS=1
export KORU_VDISPLAY_PREFER_PHOTO_VQL=auto   # JetBrains: auto gdy capture potwierdzone
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
export KORU_SRC=~/github/semcod/koru/src IMGL_SRC=~/github/semcod/imgl

koru autonomous up --project . --agent-lane=jetbrains --max-cycles 1
```

Dla ręcznego testu chatu preferuj **`koru-drive-photo-vql.sh`** — pełny audit i guardy prepare.

### Typowe problemy

| Objaw | Co zrobić |
|-------|-----------|
| `prepare_aborted: capture does not match` | Podnieś docelowe IDE na monitorze capture; sprawdź `competing_ide: Cursor` w prepare |
| `elements: 0` w observe | Ustaw `IMGL_SRC` i `pip install -e ".[observe]"` w venv vdisplay |
| `requested monitor DP-2 not connected` | `vdisplay monitors` — podaj `--source` z listy |
| Tekst w terminalu zamiast PyCharm chat | Terminal na tym samym monitorze co capture — przenieś shell |
| Drive `ok: true` ale tekst nie w IDE | Sprawdź audit: `capture_confirmed`, `verification.verified`, `inference_ok` |

Testy kontraktu (bez pulpitu): w repo koru — `pytest tests/test_photo_vql_drive.py`.

---

## PL — rozwój vdisplay przez interfejs PC

Ten komputer (nvidia, GNOME Wayland, 3 monitory) jest docelową maszyną dev. vdisplay obserwuje pulpit przez broker + keeper screencast, a planfile uruchamia regresję capture i testy.

```bash
# Terminal 1 — broker (ta sama sesja GNOME)
export PYTHONPATH=src:packages/vdisplay-agent/src
vdisplay-agent serve

# Terminal 2 — automatyzacja dev
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
export PYTHONPATH=src:packages/vdisplay-agent/src
bash examples/dev-workflow/run-dev-automation.sh
# ponowny run (zadania były już done):
bash examples/dev-workflow/run-dev-automation.sh --reset
# pętla autonomy (observe → find → act → verify):
bash examples/dev-workflow/run-dev-automation.sh --autonomy --setup-vision --reset
# cross-IDE smoke (JetBrains → Cursor, koru + vdisplay):
bash examples/dev-workflow/run-dev-automation.sh --cross-ide --reset
```

Dokumentacja: [docs/guides/gnome-wayland-screencast.md](../../docs/guides/gnome-wayland-screencast.md) · [autonomy-loop.md](../../docs/guides/autonomy-loop.md)

## Konfiguracja projektu

- **`vdisplay.yaml`** (root repo) — monitory, okna, akcje, domyślne flagi automatyzacji
- **`.vdisplay/vdisplay.override.yaml`** — opcjonalne nadpisania użytkownika (patrz `vdisplay.override.example.yaml`)
- **`.vdisplay/`** — metadane runtime: `runs/`, `observe/`, `context/`, `vql/`, `config/vdisplay.effective.json`

```bash
vdisplay config --project .
export VDISPLAY_OBSERVE=1
vdisplay auto --project . --planfile examples/dev-workflow/planfile-autonomy.yaml --source yaml run
```

## Prerequisites

```bash
cd ~/github/wronai/vdisplay
source .venv/bin/activate
pip install -e ".[pillow,dev,auto]" -e "packages/vdisplay-agent[serve]"

# Autonomy loop (vision OCR + optional map):
bash examples/dev-workflow/setup-autonomy.sh
# bash examples/dev-workflow/setup-autonomy.sh --build-map
```

## Run

```bash
# Terminal 1 — broker (same GNOME session)
export PYTHONPATH=src:packages/vdisplay-agent/src
vdisplay-agent serve

# Terminal 2 — automation
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
export PYTHONPATH=src:packages/vdisplay-agent/src
bash examples/dev-workflow/run-dev-automation.sh
```

The script checks agent health, ensures screencast is ready, then runs all tasks in `planfile.yaml`:

- preflight, screencast status, monitors, windows, app list
- probe + screenshot for DP-1, DP-2, HDMI-1
- agent health via HTTP API

Output PNGs: `/tmp/vdisplay-dev-dp1.png`, `dp2`, `hdmi1`.

## Manual commands

```bash
vdisplay auto --project . --planfile examples/dev-workflow/planfile.yaml list
vdisplay auto --project . --planfile examples/dev-workflow/planfile.yaml once
vdisplay auto --project . --planfile examples/dev-workflow/planfile.yaml run --max 3
```

## Documentation

Full guide: [docs/guides/gnome-wayland-screencast.md](../../docs/guides/gnome-wayland-screencast.md)
