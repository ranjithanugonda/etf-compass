# Action Items – Trading & Automation System

## 1. Trade Management

- Trade Book Download – Enable downloadable trade book (Excel/PDF) with date-wise filtering.

- Charges for Trade – Display detailed brokerage, taxes, exchange charges, and net P&L per trade.( need to get calculation from Pavan)

- Cancelled Orders Book – Maintain a separate log for cancelled/failed orders with timestamp and reason.

- Signals Executed (Yes/No Status) – Add execution confirmation column for generated signals.

- Time Adjustment for Buying & Selling – Allow configurable time windows for entry & exit execution.

In Screens while updating filter values in Admin settings need to update minimum 1 week record in that time and in night we need to run cron to update full history

## 2. System & Admin Controls

KATS – Admin Settings:

User access control,

strategy activation/deactivation,

Strategy parameter editing,

audit log maintenance.

Manage ETF/Stocks
ETF Addition / Deletion – Add new ETFs dynamically, remove inactive ETFs, update mapping in strategies.

Algorithm Pause / Run – Manual override option, emergency stop mechanism, scheduled pause functionality.

- Automation Filtering – Filtering based on liquidity(turnover), volatility, market cap, sector, and strategy rules.(Market cap > 999 and turnover > 9cr(turnover = closeprice * 1m volume avg)

## 3. AI & Advanced Tracking

- AI-Based Special Situation Tracker – Dhruva, Freedom & Stocki (monitor corporate actions, breakouts, unusual volumes, earnings triggers).
And How to track special situation

- Update Sector, Market Cap & Theme – Update classification for newly added stocks in Dhruva, Freedom, and Stocki models.(it will update 6 month once july mid and jan mid manualy)

- Exceptional Handling – Corporate actions and extreme market events such as merger, demerger, stock split, bonus issue, rights issue, buyback, delisting, black swan events, trading halts, circuit limits, broker/API failures, and sudden volatility spikes, with automatic system adjustments, risk control, and strategy pause mechanisms.
