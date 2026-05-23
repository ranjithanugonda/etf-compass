Product Requirements Document (PRD)

ETF Compass

“This system compounds capital by structure, not by emotion.”

Version: 1.1
Status: Approved
Market: India – Cash Market (ETFs)
Product Owner: Anand Venkitachalam
Prepared For: KARM Capital

CONTENTS

## 1. Product Overview

To build a rule-based, fully automated ETF buying system that systematically accumulates ETFs only in confirmed uptrends, deploys capital in defined tranches, avoids emotional decision-making, and exits positions solely based on profit targets. The system focuses on capital discipline, trend alignment, and long-term compounding rather than short-term market prediction.

## 2. Scope Definition

### 2.1 In Scope

Long-only ETF trading

Daily signal generation

Tranche-based accumulation

Trend-based eligibility

Profit-target exits

Reporting & alerts

### 2.2 Out of Scope

Intraday trading

Short selling

Futures & options

Stop-loss based exits

Manual overrides during live execution

## 3. ETF Universe

The system shall trade only the ETFs included in the approved universe. No ETF outside this list may be traded without formal approval. ETFs are selected based on a minimum average daily turnover of ₹5 crore and preference for the lowest available expense ratios to ensure liquidity and cost efficiency. The approved ETF universe shall be reviewed and updated on a semi-annual basis as part of the governance process.

### 3.1 Approved ETF List

| ETF Symbol | β | ATR | ETF Theme | AMC | Underlying Exposure |
| --- | --- | --- | --- | --- | --- |
| COMMODITIES | COMMODITIES | COMMODITIES | COMMODITIES | COMMODITIES | COMMODITIES |
| METALIETF | 1.36 | 13% | Nifty Metal ETF | Nippon | Metal & mining stocks |
| OILETF | 1.09 | 6% | Nifty Oil & Gas ETF | Nippon | Oil & energy sector |
| GOLDIETF | -0.06 | 13% | Gold ETF | Nippon | Physical gold |
| SILVERIETF | 0.2 | 23% | Silver ETF | ICICI Pru | Physical silver |
| SECTORAL | SECTORAL | SECTORAL | SECTORAL | SECTORAL | SECTORAL |
| FMCGIETF | 0.6 | 6% | Nifty FMCG ETF | Nippon | FMCG sector |
| PHARMABEES | 0.78 | 10% | Nifty Pharma ETF | Nippon | Pharmaceutical sector |
| CPSEETF | 1.16 | 8% | CPSE ETF | Nippon | PSU companies |
| MODEFENSE | 1.2 | 9% | Nifty India Defence ETF | Nippon | Defence & aerospace |
| MOREALTY | 1.56 | 7% | Nifty Realty ETF | Nippon | Real estate sector |
| ITBEES | 1.17 | 10% | Nifty IT ETF | Nippon | IT services |
| AUTOBEES | 1.18 | 6% | Nifty Auto ETF | Nippon | Automobile sector |
| PSUBNKBEES | 1.16 | 9% | Nifty PSU Bank ETF | Nippon | PSU banking stocks |
| BANKBEES | 0.94 | 4% | Nifty Bank ETF | Nippon | Banking sector |
| INDIAN MARKET INDEX | INDIAN MARKET INDEX | INDIAN MARKET INDEX | INDIAN MARKET INDEX | INDIAN MARKET INDEX | INDIAN MARKET INDEX |
| MIDCAETF | 1.17 | 7% | Nifty Midcap 150 ETF | ICICI Pru | Indian mid-cap stocks |
| HDFCSML250 | 1.18 | 5% | Nifty Smallcap 250 ETF | HDFC MF | Indian small-cap stocks |
| JUNIORBEES | 1.17 | 5% | Nifty Next 50 ETF | Nippon | Emerging large caps |
| SENEXIETF | 0.98 | 4% | Sensex ETF | ICICI Pru | BSE Sensex |
| NIFTYIETF | 1 | 5% | Nifty 50 ETF | ICICI Pru | Nifty 50 |
| INTERNATIONAL MARKET INDEX | INTERNATIONAL MARKET INDEX | INTERNATIONAL MARKET INDEX | INTERNATIONAL MARKET INDEX | INTERNATIONAL MARKET INDEX | INTERNATIONAL MARKET INDEX |
| HNGSNGBEES | 0.61 | 7% | Hang Seng ETF | Nippon | Hong Kong equities |
| MAFANG | 0.64 | 3% | NYSE FANG+ ETF | Motilal Oswal | US technology leaders |
| MON100 | 0.9 | 7% | Nasdaq 100 ETF | Motilal Oswal | US Nasdaq 100 |

## 4. Capital Allocation

| Parameter | Specification |
| --- | --- |
| Total Corpus | 1,50,00,000 |
| Initial Tranche | ₹3,00,000 (2%) |
| Second Tranche | ₹2,00,000 (1.33%) |
| Third Tranche | ₹1,50,000 (1%) |
| Fourth Onwards | ₹1,00,000 (0.66%) |
| Maximum Position Size (per ETF) | ₹12,50,000 (8.33%) |
| Maximum Number of Tranches | 9 |
| Position Type | Long only |
| Time Stop Loss | 4 Months |
| Duration of Add On | One Week |

## 5.   TREND Framework

The strategy uses EMA21 and EMA60 on a daily time frame to define intermediate trend alignment.

A Strong Trend is identified when price is above EMA21, EMA21 is above EMA60.

A Neutral Trend exists when price remains above EMA60 but below EMA21. In this add-ons are allowed at 50% allocation.

A Weak Trend is defined by price closing below EMA60, under which no new positions or add-ons are allowed. The existing position will be monitored.

This structured hierarchy ensures capital is deployed primarily during confirmed strength and preserved during structural deterioration.

## 6. Rules : Entry & Exit

### 5.1 Entry Rules – New Position

A new position may be initiated only if there is no existing position in the ETF and the trend qualification is valid. The trend qualification on the daily timeframe is defined as: Close Price > EMA(21) and EMA(21) > EMA(60).

A buy order shall be initiated once the pullback condition is met. A pullback is considered valid when the price has declined from the highest closing price in the relevant lookback period by at least 2.5% over the last 5 trading days (weekly pullback) or by at least 5% over the last 21 trading days (monthly pullback).

Upon satisfaction of both the trend and pullback conditions, ETF units worth ₹3,00,000 shall be purchased, and the execution price shall be recorded as the Last Buy Price (LBP).

### 5.4 Entry Rules – Additional Tranches

This rule is applicable only when an existing position is already present. An additional tranche may be initiated when the current price is less than or equal to 97.5% of the Last Buy Price (LBP), indicating a price decline of at least 2.5% from the last buy price.

Each add-on tranche shall be executed for a value of ₹1,00,000, subject to the condition that the total deployed capital does not exceed the maximum position size of ₹10,00,000. Trend qualification is not revalidated for the execution of additional tranches.

### 5.5 Exit Rules

The entire position shall be exited when the market price reaches or exceeds 105% of the weighted average buy price, resulting in a 5% profit. The exit shall be executed in a single transaction, with no partial exits and no price-based stop-loss.

A time-based exit shall apply if the profit target is not achieved within four months from the initial entry, in which case the entire position shall be exited at the prevailing market price

### 5.5 TimeFrame

The system shall scan conditions daily after market close, execute orders on the next trading day as limit orders only and restrict all trades to delivery-based execution only

## 6. Return Expectation

Based on portfolio simulations and sensitivity analysis across profit targets and holding durations, this strategy is expected to deliver stable, market-linked returns with improved capital efficiency. All return expectations are indicative in nature and subject to market conditions.

Assuming a maximum position size of ₹10 lakh per ETF, 12 concurrent positions, and an average holding period of approximately 4 months (implying ~3 capital cycles per year), the portfolio is designed to generate annualised pre-tax returns in the range of 13% to 15% under the base-case scenario. This assumes a 5% profit target per completed trade, which is statistically aligned with historical return distributions observed across broad market, sectoral, and global equity indices.

In a bear-case scenario, assuming 4% profit per trade, the portfolio is expected to generate ~11–12% annualised returns, broadly comparable to long-term index returns but with greater control over capital deployment and drawdown duration.

In the best-case scenario, assuming 6% per trade, portfolio returns can rise to ~17% per annum. Importantly, returns are highly sensitive to holding period discipline—shorter average trade durations materially improve portfolio ROI, while prolonged holding periods reduce annualised returns.

Overall, the strategy does not seek to outperform markets aggressively, but to deliver repeatable, rule-based returns with better capital velocity and risk-adjusted outcomes, positioning it as a tactical allocation overlay rather than a replacement for long-term strategic investing.

## 7. Dashboards

Three level of hierarchy Top is for decisions. Middle for Diagnostics and Bottom for evidence

https://claude.ai/chat/90332ab8-403d-4be7-80fd-8ec270183b28

Decision Dashboards

YTD ROI (%)

In Tab Include Expected ROI (%)

Color code ROI as Green or RED based on comparison with Expected ROI.

Avg Duration (M)

Average Holding Duration in months

Expected Holding period

Color code ROI as Green or RED based on comparison with Expected ROI.

Capital Utilized (%)

Monthly Dashboard

New Positions

Add-on

Exits

Time Exits

Profit Exits

Charts (rolling twelve months)

X (months)

Y ROI

### 8.1 State Management (Per ETF)

The system must track:

Position status (Active / Flat)

Total capital deployed

Tranches used

Last buy price

Weighted average cost

Unrealized P&L

Trend qualification status

### 8.2. Alerts

New position initiated

Additional tranche executed

Profit target exit

Trend filter violation (informational)

### 8.3 Reports

Daily portfolio summary

ETF-wise allocation

AMC-wise exposure (optional)

Tranche utilization

## 8. Annexure I

| ETF Category | ETFs (Illustrative) | Profit Target – 3 Months | Profit Target – 4 Months | Time-Based Review | Add-on Gap | Rationale |
| --- | --- | --- | --- | --- | --- | --- |
| Core Index ETFs | NIFTYIETF, SENSEXIETF, JUNIORBEES | 4–5% | 5–6% | 4 months | 2.5% | Stable trend behaviour, lower volatility, consistent return distribution |
| Sectoral ETFs (Momentum) | BANKBEES, METALIETF, PHARMABEES, FMCGIETF, AUTOBEES, PSUBNKBEES | 4–6% | 5–7% | 4 months | 2.5% | Higher dispersion than indices; benefit from slightly higher targets |
| Mid & Small-Cap ETFs | MIDCAPETF, HDFCSML250 | 5–6% | 6–8% | 4 months | 2.5% | Strong momentum characteristics; higher upside with acceptable volatility |
| Commodity ETFs – Gold | GOLDIETF | 3–4% | 4–5% | 3 months | 3.0% | Lower median returns, faster mean reversion, regime-driven behaviour |
| Commodity ETFs – Silver | SILVERIETF | 4–6% | 5–7% | 3 months | 3.5% | High volatility and momentum bursts; wider add-on spacing required |
| Global / Tech ETFs | MON100, MAFANG, HNGSNGBEES | 4–6% | 5–7% | 4 months | 2.5% | Higher volatility than Indian indices but strong trend persistence |
