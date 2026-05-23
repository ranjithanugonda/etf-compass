# ETF Compass — Project Conventions

This file is loaded by Claude Code at session start. It carries the rules every contributor — human or LLM — follows in this repo.

## Binding standard

[`CLAUDE coding guidelines.md`](./CLAUDE%20coding%20guidelines.md) is the **binding coding standard**. Read it before any non-trivial change. Its four principles override default impulses:

1. **Think Before Coding** — surface assumptions, ask when uncertain, never silently pick between interpretations.
2. **Simplicity First** — minimum code that solves the problem. No speculative features, no abstractions for single-use code.
3. **Surgical Changes** — touch only what the task requires.
4. **Goal-Driven Execution** — every task has an explicit "verify" step that must pass before moving on.

## What this project is

Rule-based, fully automated **ETF accumulation system** for the Indian cash market. Long-only, tranche-based, profit-target exits, no stop-loss. Generates daily signals after market close, places limit orders next day, delivery only. See [`docs/prd/etf-prd.md`](./docs/prd/etf-prd.md) for the authoritative spec.

Alongside the trading engine sits a persistent **LLM-wiki** following [Karpathy's pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f): a directory of markdown files that compounds knowledge over time. The wiki holds the *why* of every trade; Postgres holds the *what*. See [`WIKI_SCHEMA.md`](./WIKI_SCHEMA.md).

## Architecture in one paragraph

Raw sources (yfinance OHLC → parquet, paper broker fills → Postgres, corp actions → disk) feed two parallel sinks: a **reporting layer** (pandas + SQL → dashboards via FastAPI) and the **LLM-wiki** (Claude Sonnet writes per-ETF pages, daily logs, decision rationales; Claude Opus answers queries). React frontend reads the API.

## Authoritative specs (read before coding)

- [`docs/prd/etf-prd.md`](./docs/prd/etf-prd.md) — trading rules, capital allocation, ETF universe, dashboard requirements
- [`docs/action-items/action-items.md`](./docs/action-items/action-items.md) — KATS admin controls, charges, special situations, exception handling
- [`WIKI_SCHEMA.md`](./WIKI_SCHEMA.md) — wiki page templates, link conventions, log.md prefix format
- Plan: `C:\Users\ranjith.k.anugonda\.claude\plans\i-want-to-build-vast-whisper.md`

## Resolved ambiguities & design rules

- **Max position size & tranche sizes are configurable, not hard-coded** (resolved 2026-05-22). Strategy parameters live in the `strategy_params` table and are editable via the KATS admin UI. The `capital_allocator` validates that the configured tranche schedule is consistent with the configured max position size — if a user shrinks the max, the allocator auto-clips the number of tranches that fit. PRD §4 values (max ₹12,50,000; tranches 3L / 2L / 1.5L / 1L / …) are the **defaults**, not the only valid values.

## Runtime

- Python 3.14 via `C:\Users\ranjith.k.anugonda\OneDrive - Accenture\Documents\PyCoding\.314env\Scripts\python.exe`
- Postgres 16, Redis 7 (Docker or native — see `README.md`)
- All times Asia/Kolkata; EOD scan 16:00 IST, morning execute 09:20 IST

## Conventions

- Trading-rule code under `backend/app/strategy/` must be **pure** (no I/O, no DB, no time). This is the testability + backtest guarantee.
- All migrations via Alembic. No raw `CREATE TABLE` in app code.
- Wiki writes are atomic (write to temp, fsync, rename). Never partial-write a wiki file.
- Secrets via `.env` (local) or K8s `Secret` (prod). Never check secrets into git.
- Tests: `pytest tests/strategy/` is the gate before any rule change merges.
