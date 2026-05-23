# WIKI_SCHEMA — Karpathy LLM-Wiki for ETF Compass

This file defines the structure and conventions for the markdown wiki under [`wiki/`](./wiki/). The wiki is the **narrative truth** of the system: it records *why* every signal and trade happened, and it accumulates across runs.

The wiki is read and written by the LLM (Anthropic Claude). Treat this schema as the contract — the LLM follows it, humans browse the result, dashboards link into it.

## Three layers (Karpathy)

1. **Raw sources** (immutable, outside `wiki/`): OHLC parquet under `data/ohlc/`, paper-broker fills in Postgres, corporate-actions feed under `data/corp_actions/`. The LLM reads these; it never modifies them.
2. **Wiki** (mutable, compounding): the `wiki/` directory. Updated by the ingest job; queried by users via the WikiQuery UI.
3. **Schema**: this file. Defines page templates, link conventions, and the log prefix format. Loaded into every LLM prompt as cached context.

## Directory layout

```
wiki/
├── index.md                          catalog of all pages, updated every ingest
├── log.md                            append-only timeline of every system event
├── etfs/
│   └── {SYMBOL}.md                   per-ETF state + history + rationale (e.g. MIDCAETF.md)
├── decisions/
│   └── {YYYY-MM-DD}-{SYMBOL}-{action}.md   one page per concrete signal/trade
├── daily/
│   └── {YYYY-MM-DD}.md               EOD scan summary for the whole portfolio
├── special-situations/
│   └── {YYYY-MM-DD}-{SYMBOL}-{event}.md    corp actions, halts, black swans
└── reviews/
    └── H{1|2}-{YYYY}.md              semi-annual ETF universe governance review
```

## log.md prefix format

Every line in `log.md` starts with this prefix so Unix tools (`grep`, `awk`) can slice it cleanly:

```
## [YYYY-MM-DD] {EVENT} | {SYMBOL} | {detail}
```

`EVENT` is one of:

- `INGEST` — daily OHLC and corp-actions absorbed
- `SCAN` — EOD scan completed for the universe
- `SIGNAL` — engine emitted a signal (`detail` = `ENTRY` / `ADDON` / `EXIT-PROFIT` / `EXIT-TIME`)
- `ORDER` — broker order placed (`detail` includes order id and limit price)
- `FILL` — order filled (`detail` includes fill price and qty)
- `CANCEL` — order cancelled (`detail` includes reason)
- `TREND` — trend regime changed (`detail` = `Strong→Neutral` etc.)
- `CORP` — corporate action (split, bonus, dividend, merger, delisting)
- `EXCEPTION` — exception handler triggered (halt, circuit, broker outage)
- `LINT` — nightly lint run with findings count

Example:
```
## [2026-05-22] SIGNAL | MIDCAETF | ENTRY tranche 1 — trend Strong, pullback 3.1% in 5d → [[2026-05-22-MIDCAETF-entry]]
```

## index.md format

One section per category, each entry one line: `- [Title](relative/path.md) — one-line summary`. The ingest job rebuilds the entire file from the directory listing on every run, so manual edits will be overwritten — point fixes belong in the individual page.

## Page templates

### `etfs/{SYMBOL}.md`

```markdown
# {SYMBOL} — {Theme} ({AMC})

- **Category:** {Commodities | Sectoral | Core Index | Mid/Small | Global}
- **β / ATR:** {beta} / {ATR}
- **Underlying exposure:** {…}

## Current state (as of {YYYY-MM-DD})
- **Position status:** {Active | Flat}
- **Tranches used:** {n} / 9
- **Capital deployed:** ₹{x}
- **Last buy price (LBP):** ₹{x}
- **Weighted average cost (WAC):** ₹{x}
- **Unrealized P&L:** ₹{x} ({%})
- **Trend regime:** {Strong | Neutral | Weak}

## Why we are (or are not) in this ETF
{LLM-written narrative tying current state to the most recent decision page.}

## Decision history
- [[{decision-page}]]
- [[{decision-page}]]

## Special situations
- [[{situation-page}]] — {one-line}
```

### `decisions/{YYYY-MM-DD}-{SYMBOL}-{action}.md`

```markdown
# {SYMBOL} {ACTION} — {YYYY-MM-DD}

- **Action:** {ENTRY | ADDON | EXIT-PROFIT | EXIT-TIME}
- **Trigger:** {short reason from the rule that fired}
- **Trade IDs:** {linked to DB rows}

## Inputs
- **Trend:** {regime} (price {x}, EMA21 {y}, EMA60 {z})
- **Pullback:** {pct} over {days}d
- **LBP / WAC before action:** ₹{x} / ₹{y}
- **Capital state:** {tranches used}/9, deployed ₹{x} of max ₹{max}

## Rule cited
{One-line excerpt from PRD §5.1 / §5.4 / §5.5}

## Outcome (filled by morning_execute or by EOD recap)
- **Limit price:** ₹{x}
- **Filled at:** ₹{x} on {YYYY-MM-DD}
- **Tranche size:** ₹{x}

## Related
- [[etfs/{SYMBOL}]]
- Previous: [[{prev-decision}]]
```

### `daily/{YYYY-MM-DD}.md`

```markdown
# Daily scan — {YYYY-MM-DD}

## Headline numbers
- New positions: {n}
- Add-ons: {n}
- Profit exits: {n}
- Time exits: {n}
- Capital utilised: {%}

## Per-ETF changes
{table or list, only the ETFs whose state changed today}

## Trend regime transitions
{symbol — old → new}

## Notes
{LLM-written 2–3 sentence summary tying today to recent context}
```

### `special-situations/{YYYY-MM-DD}-{SYMBOL}-{event}.md`

```markdown
# {SYMBOL} — {Event} on {YYYY-MM-DD}

- **Event type:** {split | bonus | dividend | merger | delisting | halt | circuit | broker-outage | volatility-spike}
- **Source:** {feed reference}
- **System action:** {paused | adjusted-WAC | re-ran-engine | none}

## Detail
{LLM-written, citing the source feed entry}

## Affected pages
- [[etfs/{SYMBOL}]]
- [[decisions/...]]  (if any open position was touched)
```

### `reviews/H{1|2}-{YYYY}.md`

Semi-annual governance review (PRD §3 says the universe is re-validated twice a year). Lists adds, drops, and the rationale, with links to liquidity / expense-ratio evidence.

## Linking convention

- Use `[[wiki-relative-path]]` for internal links — the WikiBrowser resolves these.
- Use full `[Title](./path)` for external links (e.g. citing PRD sections).
- Every decision page **must** link back to its ETF page; every ETF page **must** list its decision history.
- The lint job flags pages that violate either invariant.

## Atomicity

Writes go via temp file + `os.replace` so a crashed ingest never leaves a half-written page. The wiki directory is on a persistent volume in production (K8s PVC).
