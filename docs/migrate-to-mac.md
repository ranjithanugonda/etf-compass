# Migrating ETF Compass to a Mac (mini / laptop)

Use this guide when moving the project off a company-managed Windows machine (where Docker Desktop / WSL 2 / Hyper-V may be blocked) onto a personal macOS device.

## What's portable vs not

| Item | Portable? | Notes |
|---|---|---|
| Everything in `raj-project/` (code, configs, docs, wiki, source `.docx`) | Yes | Plain text/markdown/Python/YAML — no platform code |
| `pyproject.toml`, `docker-compose.yml`, `.env.example`, `WIKI_SCHEMA.md` | Yes | Path-independent |
| The Windows `.314env` virtualenv | No | Windows binaries. Recreate on Mac via `python -m venv`. |
| `scripts/extract_docx.py` | Yes | Uses `Path(__file__).resolve().parent` — works on any OS |
| `~/.claude/` memory + plan files | Optional | Copy across only if you want Claude Code to retain prior session context (recommended) |

Two files in the repo currently reference the Windows-specific Python path (`README.md` and `CLAUDE.md`). They are documentation only, not code. Update them once on the Mac so `python` (from the activated venv) replaces the long `OneDrive/...` path.

---

## Step-by-step

### 1. Move the files

**Option A — Git (recommended)** — gives you history and a real backup:

```powershell
# On Windows, from c:\Users\ranjith.k.anugonda\raj-project
git init
git add .
git commit -m "phase 0b: scaffold"
# Create a private repo on github.com / gitlab / bitbucket, then:
git remote add origin git@github.com:<you>/etf-compass.git
git push -u origin main
```

```bash
# On Mac
git clone git@github.com:<you>/etf-compass.git ~/projects/etf-compass
```

**Option B — Direct copy** — faster, no git server needed:

- Zip `raj-project/` on Windows
- Transfer via AirDrop / iCloud Drive / USB / network share
- Unzip into `~/projects/etf-compass/` on the Mac

The full repo (including the two source `.docx` files) is well under 1 MB.

### 2. Install macOS prerequisites

```bash
# Homebrew (skip if already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Python 3.13 — pyproject.toml requires >=3.13
brew install python@3.13

# Docker Desktop for Mac (free, no corporate restrictions on personal hardware)
brew install --cask docker
# Launch Docker.app once from /Applications to complete first-run setup.

# Node.js — only needed when the frontend lands (Phase 6)
brew install node@20
```

On Apple Silicon (M1/M2/M3/M4) all of the above run natively. Docker on macOS is materially smoother than on locked-down corporate Windows.

### 3. Recreate the Python environment

```bash
cd ~/projects/etf-compass
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

That single `pip install` reads `pyproject.toml` and pulls in FastAPI, SQLAlchemy, Anthropic SDK, yfinance, pandas, python-docx, pytest, ruff, mypy, etc.

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY and POSTGRES_PASSWORD at minimum.
```

### 5. Boot the infra services

```bash
docker compose up -d
docker compose ps        # both postgres and redis should report "healthy"
```

### 6. Smoke tests

```bash
# Regenerate the docx-to-markdown specs (should be byte-identical to what was committed)
python scripts/extract_docx.py

# Postgres reachable
docker compose exec postgres psql -U etf_compass -d etf_compass -c "SELECT 1"

# Redis reachable — should reply PONG
docker compose exec redis redis-cli ping
```

If all three pass, the Mac is ready for Phase 1 (DB models + Alembic + OHLC backfill).

### 7. (Optional) Bring Claude Code session memory across

If you want Claude Code on the Mac to remember the prior conversation context — the binding to `CLAUDE coding guidelines.md`, the strategy-params-configurable decision, the approved plan — copy these two locations as well:

| What | Windows source | Mac destination |
|---|---|---|
| Project memory | `C:\Users\ranjith.k.anugonda\.claude\projects\c--Users-ranjith-k-anugonda-raj-project\` | `~/.claude/projects/<auto-named-dir>/` |
| Plan file | `C:\Users\ranjith.k.anugonda\.claude\plans\i-want-to-build-vast-whisper.md` | `~/.claude/plans/i-want-to-build-vast-whisper.md` |

The Mac project memory directory name will be auto-generated from the new project path (e.g. `-Users-<you>-projects-etf-compass`). Easiest path: open the project once in Claude Code on the Mac — it creates the directory — then drop the contents of the Windows project memory into it. The `MEMORY.md` index and the individual feedback files will be picked up next session.

### 8. Update path references

Edit two doc files once on the Mac:

- `README.md` — replace the Windows Python path in the "Prerequisites" and "Extracting the source specs" sections with `python` (assumes the venv is activated).
- `CLAUDE.md` — replace the same Windows path in the "Runtime" section.

No code changes required — `scripts/extract_docx.py` and `pyproject.toml` are already platform-agnostic.

---

## Resulting layout on the Mac

```
~/projects/etf-compass/
├── .venv/                    (recreated locally; not in git)
├── .env                      (copied from .env.example, not in git)
├── CLAUDE.md
├── CLAUDE coding guidelines.md
├── README.md
├── WIKI_SCHEMA.md
├── docker-compose.yml
├── pyproject.toml
├── docs/
├── scripts/
├── wiki/
└── ...
```

Phase 1 onwards proceeds identically to the Windows path described in the main plan — only the host OS changes.

---

## When to use this guide vs the main README

- **Main `README.md`** — daily-driver instructions for whichever machine you're running on.
- **This file** — one-time migration steps. Once you're settled on the Mac, the main README is sufficient.
