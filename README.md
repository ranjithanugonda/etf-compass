# ETF Compass

Rule-based, fully automated ETF accumulation system for the Indian cash market, with a persistent LLM-wiki that remembers *why* every trade was taken.

> "This system compounds capital by structure, not by emotion."
> — PRD v1.1

## What it does

- Scans 21 approved ETFs daily after market close (Asia/Kolkata, 16:00 IST)
- Generates buy / add-on / exit signals using a trend filter (EMA21/EMA60), pullback detection, and tranche-based capital allocation
- Places next-day limit orders (paper-trading by default; real broker pluggable later)
- Exits only on **5 % profit over weighted-average cost** or a **4-month time stop** — no stop-loss
- Maintains a markdown wiki (Karpathy LLM-wiki pattern) that records every signal, every decision, every rationale
- Surfaces three dashboards: **Decision** (ROI, capital utilisation), **Diagnostic** (monthly activity, equity curve), **Evidence** (positions, trades, wiki pages)

Full spec: [`docs/prd/etf-prd.md`](./docs/prd/etf-prd.md).
Project conventions: [`CLAUDE.md`](./CLAUDE.md).

## Prerequisites

- **Python 3.14** — the existing env at `C:\Users\ranjith.k.anugonda\OneDrive - Accenture\Documents\PyCoding\.314env` is used by default.
- **Postgres 16** + **Redis 7** — see "Run path" below for two installation options.
- **Node.js 20 LTS** — only required when the frontend lands (Phase 6 of the plan).
- **`ANTHROPIC_API_KEY`** — for the LLM-wiki. Sign up at <https://console.anthropic.com>. Skip if running with the LLM disabled.

## Run path A — Docker Desktop (recommended)

1. Install **Docker Desktop for Windows** from <https://docker.com/products/docker-desktop>. The installer enables WSL 2 automatically; accept it. If WSL 2 is missing, open an elevated PowerShell, run `wsl --install`, and reboot.
2. Launch Docker Desktop. Settings → Resources → at least **4 GB RAM and 2 CPUs**.
3. Verify: `docker --version` and `docker compose version` both print versions.
4. From the project root:
   ```powershell
   copy .env.example .env
   # edit .env, set ANTHROPIC_API_KEY and POSTGRES_PASSWORD
   docker compose up -d
   ```
5. Postgres listens on `localhost:5432`, Redis on `localhost:6379`. Backend and frontend services will be added in later phases.

> **Accenture-managed-laptop note:** Hyper-V / WSL 2 may be locked down. If the installer fails, raise an IT ticket for "Docker Desktop for Developer use" or fall back to Run path B.

## Run path B — Native (no Docker)

1. Install **PostgreSQL 16** from <https://postgresql.org/download/windows> (EDB installer). Default port 5432. Remember the password.
2. Install **Redis** for Windows via **Memurai** (free Developer edition) from <https://memurai.com>. *(Or skip Redis for the MVP — the queue can run in-memory.)*
3. Install **Node.js 20 LTS** from <https://nodejs.org> (only when the frontend lands).
4. Copy `.env.example` to `.env` and fill in `POSTGRES_*` to point at your local Postgres, plus `ANTHROPIC_API_KEY`.
5. Backend and frontend will run directly from the `.314env` virtualenv and `frontend/`; instructions added in Phase 1 and Phase 6 respectively.

Same MVP either way. Docker just packages it for the K8s path.

## Project layout (target state)

See the approved plan at `C:\Users\ranjith.k.anugonda\.claude\plans\i-want-to-build-vast-whisper.md`. Files are added phase-by-phase rather than pre-scaffolded.

## Phases (current status)

| Phase | What | Status |
|---|---|---|
| 0a | Prereqs / dev env walkthrough | Done (this README) |
| 0b | Scaffold (this commit) | **In progress** |
| 1  | DB models + OHLC ingestion | Pending |
| 2  | Strategy engine + backtest gate | Pending |
| 3  | Paper broker + scheduled jobs | Pending |
| 4  | LLM-wiki (Anthropic) | Pending |
| 5  | FastAPI + JWT auth | Pending |
| 6  | React dashboards | Pending |
| 7  | Docker images + K8s manifests | Pending |
| 8  | Backtest UI + polish | Pending |

## Extracting the source specs

The two source `.docx` files in this repo are converted to markdown by:

```powershell
& "C:/Users/ranjith.k.anugonda/OneDrive - Accenture/Documents/PyCoding/.314env/Scripts/python.exe" scripts/extract_docx.py
```

Outputs land in `docs/prd/` and `docs/action-items/`.

## License & ownership

Private. Product Owner: Anand Venkitachalam. Prepared for KARM Capital.
