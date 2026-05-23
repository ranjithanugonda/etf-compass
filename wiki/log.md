# ETF Compass — Event Log

Append-only chronological timeline of every system event. See [`../WIKI_SCHEMA.md`](../WIKI_SCHEMA.md) for the `## [YYYY-MM-DD] EVENT | SYMBOL | detail` prefix format.

Slice with Unix tools:
```bash
grep "^## \[2026-05" wiki/log.md             # one month
grep "SIGNAL | MIDCAETF" wiki/log.md         # one ETF's signals
grep "EXIT-PROFIT" wiki/log.md               # all profitable exits
```
## [2026-05-23] BACKTEST | ALL | 21 ETFs, 59 trades, win rate 83%, total P&L ₹616,783
## [2026-05-23] DECISION | ALL | Phase 8.5 — Added stop-loss exit (EXIT_SL, 5% default), fixed lot sizing (round() for whole shares), configurable backtest with start date/corpus, trade timeline now shows deployed capital and units per trade
## [2026-05-23] FIX | ALL | PostgreSQL enum migration — added EXIT_SL to tradeaction type. SQLAlchemy uses member NAME (uppercase) not value for enum queries.
## [2026-05-23] ANALYSIS | ALL | Capital allocation audit — 20.5% utilization (₹30.7L of ₹1.5Cr). 9 holding, 5 flat (STRONG trend but no pullback), 7 never entered (4 no OHLC data, 3 never had trend+pullback align). Root cause: dual filter (STRONG + pullback) is narrow in bull markets. See [[decisions/2026-05-23-capital-allocation-analysis]]
