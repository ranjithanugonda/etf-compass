# ETF Compass

Rule-based, fully automated ETF accumulation system for the Indian cash market, with a persistent LLM-wiki that remembers *why* every trade was taken.

> "This system compounds capital by structure, not by emotion."

## Quick Start (Docker)

```bash
# 1. Start Postgres & Redis
docker run -d --name etf-postgres -p 5432:5432 \
  -e POSTGRES_USER=etf_compass -e POSTGRES_PASSWORD=change_me \
  -e POSTGRES_DB=etf_compass postgres:16

docker run -d --name etf-redis -p 6379:6379 redis:7

# 2. Create .env
cp .env.example .env
# Edit .env — set POSTGRES_HOST=host.docker.internal, REDIS_HOST=host.docker.internal

# 3. Run the app
docker run -d --name etf-compass -p 7778:8080 \
  -e POSTGRES_HOST=host.docker.internal \
  -e REDIS_HOST=host.docker.internal \
  ranjithanugonda/etf-compass:latest

# 4. Initialize DB schema (first time only)
docker exec etf-postgres psql -U etf_compass -d etf_compass \
  -f /path/to/schema.sql  # or run alembic upgrade head

# 5. Ingest OHLC data & seed ETFs (first time only)
curl -X POST http://localhost:7778/api/admin/seed-data

# 6. Open http://localhost:7778
```

## What's inside

| Layer | Stack |
|-------|-------|
| Backend | Python 3.13, FastAPI, SQLAlchemy async, Alembic |
| Frontend | React 19, TypeScript, Vite 8, Tailwind 4, lightweight-charts v5 |
| Storage | PostgreSQL 16, Redis 7, Parquet files |
| Strategy | Pure engine — trend (EMA21/60), pullback, DCA add-ons, profit/stop-loss/time exits |
| Wiki | Karpathy LLM-wiki pattern — markdown files compound knowledge over time |

## Dashboards

- **Decision** — YTD ROI, capital utilization, holding duration KPIs
- **Backtest** — Configurable date/corpus, portfolio allocation chart, per-ETF performance, currently holding
- **Diagnostic** — Monthly ROI chart, activity table with live/backtest toggle, ETF filter
- **Evidence** — Active positions (clickable → trade history), recent trades, wiki page links
- **Trading** — Manual paper trade placement (entry/addon/exit)
- **Admin** — Strategy params, ETF manager, job triggers (backtest/EOD scan/morning execute), audit log

## Strategy Rules

| Rule | Condition | Action |
|------|-----------|--------|
| Entry | STRONG trend (close > EMA21 > EMA60) + pullback (2.5% weekly or 5% monthly) | Buy Tranche 1: ₹3,00,000 |
| Add-on | Close ≤ LBP × 0.975 + within window + tranches remaining | Buy next tranche (₹2L / ₹1.5L / ₹1L…) |
| Profit Exit | Close ≥ WAC × 1.05 | Sell entire position |
| Stop-Loss | Close ≤ WAC × (1 − stop_loss_pct) | Sell entire position |
| Time Exit | Held ≥ 4 months without other exit | Sell entire position |

All rules configurable in Admin → Strategy Params.

## Project layout

```
├── backend/app/
│   ├── strategy/     # Pure engine (no I/O, no DB)
│   ├── broker/       # Paper broker + state loader
│   ├── backtest/     # Bar-by-bar replay engine
│   ├── routers/      # FastAPI endpoints
│   ├── models/       # SQLAlchemy ORM models
│   ├── wiki/         # Wiki writer + indexer
│   └── jobs/         # EOD scan, morning execute
├── frontend/src/     # React SPA
│   └── components/   # 6 dashboards + ETF detail modal
├── wiki/             # LLM-readable knowledge base
│   ├── etfs/         # Per-ETF pages (position state, trade history)
│   ├── decisions/    # Per-trade decision pages
│   ├── daily/        # EOD scan summaries
│   └── backtest/     # Backtest aggregate results
├── docs/prd/         # Authoritative spec
└── data/             # Parquet OHLC + backtest cache (gitignored)
```

## Development

```bash
# Backend
python -m venv .venv && source .venv/bin/activate
pip install -e .
uvicorn backend.app.main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev

# Tests
pytest backend/tests/ -v
ruff check . && mypy backend/
```
