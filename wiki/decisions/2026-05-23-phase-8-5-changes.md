# Phase 8.5 Changes — 2026-05-23

## Stop-Loss Exit (EXIT_SL)

- Added `stop_loss_pct` (default 5.0) to StrategyParams — configurable via Admin UI
- New exit type: `EXIT_SL`, checked between profit exit and time exit
- Condition: `close <= WAC * (1 - stop_loss_pct / 100)`
- Priority order: Profit Exit → Stop Loss → Time Exit
- Impact on backtest: 84 total trades (up from 59), win rate dropped to 58.3%, P&L dropped to ₹87K. 10 ETFs had SL exits triggered (MOREALTY, SILVERIETF, HNGSNGBEES worst hit).
- All code paths updated: SignalAction enum, TradeAction enum, exit.py, paper_broker.py, backtest runner, wiki logger, EOD scan, dashboard counting
- PostgreSQL enum requires explicit `ALTER TYPE tradeaction ADD VALUE 'EXIT_SL'` migration

## Lot Sizing Fix

- `round()` replaces `int()` for share calculation: `units = round(tranche_amount / price)`
- This centers deployed capital around the target instead of always under-deploying
- Example: ₹300K ÷ ₹92.51 = 3242.9 shares → round() buys 3243 (₹300,010 deployed) vs int() buys 3242 (₹299,917)
- Backtest runner and paper_broker both updated
- `total_capital_deployed` now uses actual `units * price`, not theoretical `signal.tranche_amount`
- Trade timeline now shows "Deployed" (actual capital) and "Units" (whole shares) columns

## PostgreSQL Enum Migration Trap

When adding a new value to a SQLAlchemy StrEnum mapped to a PostgreSQL enum type:
- SQLAlchemy sends the Python member **NAME** (e.g., `EXIT_SL`), not the **value** (e.g., `exit_sl`)
- The DB enum value must match the Python member name in case — UPPERCASE
- Adding to the Python model alone causes "invalid input value for enum" errors at runtime
- Fix: `ALTER TYPE tradeaction ADD VALUE 'EXIT_SL'` on the database
- For fresh deployments, the Alembic migration must include all enum values

## Re-Entry Criteria

- After a position exits, re-entry uses the same 3 conditions: STRONG trend + pullback detected + no active position
- No cooldown period — re-entry possible the next trading day
- Same-day exit and entry cannot happen because the scanner returns immediately after an exit signal
- Example: CPSEETF exited at ₹101.05 on 17-Feb-2026, has not re-entered since because either trend degraded to NEUTRAL or no pullback occurred despite STRONG trend

## Configurable Backtest

- Start date picker and total corpus input added to Backtest Dashboard
- `run_backtest` accepts optional `start_date` — only processes bars on/after that date
- `run_backtest_all` passes through to all symbols
- Backtest starts flat at start_date (no prior positions carried forward)
- Admin endpoint `POST /api/admin/run-backtest` accepts `{start_date, total_corpus}` JSON body
- Summary API returns `currently_holding` (open positions) and `total_corpus`

## Rule: All Trade Decisions Are Daily Close-Based

- Scanner uses `bars[-1]` (latest daily bar) for all decisions
- Trend: `determine_trend(latest.close, latest.ema21, latest.ema60)`
- Exit: `latest_close >= WAC * 1.05` (profit) or `latest_close <= sl_price` (stop-loss)
- Entry: `latest_close` used as limit price
- This is EOD only — no intraday decisions
