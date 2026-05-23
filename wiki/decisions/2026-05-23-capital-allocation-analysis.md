# Capital Allocation Analysis — 2026-05-23

## Context

Backtest over ~2 years (2024–2026) shows only 20% capital utilization. Of ₹1.5Cr corpus, ₹30.7L is deployed across 9 ETFs, leaving ₹1.19Cr idle. Investigation into why 12 out of 21 ETFs are uninvested.

## Current State

| Status | Count | ETFs |
|--------|-------|------|
| Holding | 9 | GOLDIETF, SILVERIETF, PSUBNKBEES, MAFANG, HNGSNGBEES, METALIETF, MOREALTY, JUNIORBEES, HDFCSML250 |
| Flat (exited, not re-entered) | 5 | CPSEETF, PHARMABEES, ITBEES, MON100, AUTOBEES |
| Never entered | 7 | BANKBEES, FMCGIETF, MIDCAETF, MODEFENSE, NIFTYIETF, OILETF, SENEXIETF |

Capital deployed: ₹30.7L (20.5% of ₹1.5Cr corpus)

## Root Cause Analysis

### 4 ETFs: No OHLC Data

MIDCAETF, MODEFENSE, OILETF, SENEXIETF have zero OHLC bars in the database. These ETFs were never ingested — the yfinance pipeline did not fetch them. Without price data, the strategy cannot evaluate them.

**Fix:** Re-run OHLC ingestion for these symbols.

### 3 ETFs: Never Met Entry Conditions

BANKBEES, FMCGIETF, NIFTYIETF have full OHLC data. Over the 2-year simulation:

| ETF | STRONG days | NEUTRAL days | WEAK days | Current Trend |
|-----|-------------|--------------|-----------|---------------|
| BANKBEES | 248 (50%) | 64 (13%) | 184 (37%) | WEAK |
| FMCGIETF | 163 (33%) | 52 (11%) | 277 (56%) | WEAK |
| NIFTYIETF | 205 (42%) | 86 (17%) | 201 (41%) | WEAK |

All three had significant STRONG periods (33-50% of days). However, entry requires STRONG trend AND a pullback (2.5% weekly or 5% monthly) simultaneously. These two conditions never coincided for these ETFs during the backtest window.

### 5 ETFs: Exited But Can't Re-Enter

| ETF | Last Exit | Current Trend | Weekly Pullback | Blocker |
|-----|-----------|---------------|-----------------|---------|
| PHARMABEES | Profit exit | **STRONG** | 1.2% | Pullback too shallow (< 2.5%) |
| MON100 | Profit exit | **STRONG** | 0% | At all-time highs, no dip |
| CPSEETF | Profit exit (17 Feb 2026) | NEUTRAL | 1.0% | Trend not STRONG, close < EMA21 |
| AUTOBEES | SL exit | WEAK | 0.1% | Trend not STRONG |
| ITBEES | SL exit | WEAK | 1.3% | Trend not STRONG |

PHARMABEES and MON100 are in strong uptrends — the strategy is correctly waiting for a pullback. CPSEETF is in a mild correction (NEUTRAL). AUTOBEES and ITBEES are in downtrends (WEAK).

## Entry Rule: The Gatekeeping Mechanism

Current entry requires ALL of:
1. STRONG trend (close > EMA21 > EMA60)
2. Pullback detected (weekly: 2.5% drop from 5-day high, OR monthly: 5% drop from 21-day high)
3. No active position

This is a dual filter. Both conditions must be true simultaneously. The analysis shows:
- Many ETFs have STRONG trend WITHOUT pullback (PHARMABEES, MON100)
- Some ETFs have pullback WITHOUT STRONG trend (CPSEETF)
- The intersection is narrow — only 14 out of 21 ETFs ever entered

## Recommendations

### Immediate: Fix Missing Data

Re-run OHLC ingestion for MIDCAETF, MODEFENSE, OILETF, SENEXIETF. This adds 4 more ETFs to the eligible pool.

### Strategic Options for Relaxing Entry

**Option A: Allow NEUTRAL trend entries**
- Change entry gate from STRONG-only to STRONG or NEUTRAL
- NEUTRAL = close > EMA60 (still above the longer-term average)
- Would immediately make CPSEETF eligible
- Trade-off: lower quality entries, potentially more losing trades

**Option B: Lower pullback threshold**
- Reduce weekly pullback from 2.5% → 1.5%
- Reduce monthly pullback from 5.0% → 3.0%
- Would make PHARMABEES eligible immediately
- Trade-off: more frequent entries, buying into shallower dips

**Option C: Both (A + B)**
- NEUTRAL trend allowed + lower pullback thresholds
- Maximum capital deployment, but lowest signal quality

**Option D: No change**
- Strategy logic is sound — it entered 14 out of 17 ETFs with data (82% coverage)
- Low utilization is partly because we're at the end of a 2-year bull run where most ETFs are at highs
- DCA add-ons on existing 9 holdings will deploy more capital as pullbacks occur

## Key Insight

The strategy is performing as designed — it enters on quality setups, not to deploy capital. Low utilization is a feature in strong bull markets (nothing to buy at a discount) and a signal to consider relaxing criteria in sideways/corrective markets. The decision should be based on risk tolerance: more entries = more opportunities but potentially more stop-loss exits.

## Related

- [[2026-05-23-phase-8-5-changes]] — Stop-loss exit and lot sizing changes
- [[etfs/CPSEETF]] — Example of exited-and-flat ETF
