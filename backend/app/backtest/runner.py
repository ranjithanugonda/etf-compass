"""Pure backtest engine — replays OHLC history through the strategy engine.

No DB writes. All simulation is in-memory using the same dataclasses as live trading.
"""

from dataclasses import dataclass, field
from datetime import date

from backend.app.broker.state_loader import get_active_symbols, load_ohlc_bars, load_strategy_params
from backend.app.strategy.models import (
    PositionState,
    Signal,
    SignalAction,
    StrategyParams,
)
from backend.app.strategy.scanner import scan_etf


@dataclass
class BacktestTrade:
    symbol: str
    action: str
    entry_date: date
    exit_date: date | None = None
    entry_price: float = 0.0
    exit_price: float | None = None
    tranche_amount: float = 0.0
    units: float = 0.0
    pnl: float | None = None
    pnl_pct: float | None = None
    hold_days: int | None = None


@dataclass
class BacktestResult:
    symbol: str
    trades: list[BacktestTrade] = field(default_factory=list)
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    total_return_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    avg_hold_days: float = 0.0


def _apply_signal_in_memory(
    signal: Signal, position: PositionState, trade_date: date,
) -> BacktestTrade:
    """Simulate trade execution without touching the database.

    Uses whole-share (integer) units to match real trading — fractional
    units are not possible in delivery-based cash market.
    """
    price = signal.limit_price
    units = round(signal.tranche_amount / price) if price > 0 else 0
    actual_deployed = units * price

    trade = BacktestTrade(
        symbol=signal.symbol,
        action=signal.action.value,
        entry_date=trade_date,
        entry_price=price,
        tranche_amount=actual_deployed,
        units=units,
    )

    if signal.action == SignalAction.ENTRY:
        position.status = "active"
        position.tranches_used = 1
        position.total_capital_deployed = actual_deployed
        position.total_units = units
        position.last_buy_price = price
        position.weighted_avg_cost = price
        position.entered_at = trade_date

    elif signal.action == SignalAction.ADDON:
        old_wac = position.weighted_avg_cost or price
        old_units = position.total_units
        position.total_units += units
        position.total_capital_deployed += actual_deployed
        position.weighted_avg_cost = (
            (old_wac * old_units + price * units) / position.total_units
        )
        position.last_buy_price = price
        position.tranches_used += 1
        position.last_addon_date = trade_date

    elif signal.action in (SignalAction.EXIT_PROFIT, SignalAction.EXIT_TIME, SignalAction.EXIT_SL):
        trade.exit_date = trade_date
        trade.exit_price = price
        if position.weighted_avg_cost and position.weighted_avg_cost > 0:
            trade.pnl = (price - position.weighted_avg_cost) * position.total_units
            trade.pnl_pct = (price - position.weighted_avg_cost) / position.weighted_avg_cost * 100
        if position.entered_at:
            trade.hold_days = (trade_date - position.entered_at).days
        # Reset position
        position.status = "flat"
        position.tranches_used = 0
        position.total_capital_deployed = 0
        position.total_units = 0
        position.last_buy_price = None
        position.weighted_avg_cost = None
        position.entered_at = None
        position.last_addon_date = None

    return trade


async def run_backtest(
    symbol: str,
    params: StrategyParams | None = None,
    start_date: date | None = None,
) -> BacktestResult:
    """Run backtest for a single ETF symbol.

    If start_date is provided, only bars on or after that date are processed.
    The position starts flat at start_date (no prior positions carried forward).
    """
    if params is None:
        params = await load_strategy_params()

    bars = await load_ohlc_bars(symbol, lookback_days=9999)
    if start_date is not None:
        bars = [b for b in bars if b.date >= start_date]
    if len(bars) < 60:
        return BacktestResult(symbol=symbol)

    position = PositionState()
    trades: list[BacktestTrade] = []
    equity_peak = 0.0
    cumulative_pnl = 0.0
    max_drawdown = 0.0

    for i in range(60, len(bars)):
        window = bars[: i + 1]
        bar_date = window[-1].date
        signals = scan_etf(symbol, window, position, bar_date, params)

        for signal in signals:
            trade = _apply_signal_in_memory(signal, position, bar_date)
            trades.append(trade)

            if trade.pnl is not None:
                cumulative_pnl += trade.pnl
                equity_peak = max(equity_peak, cumulative_pnl)
                drawdown = equity_peak - cumulative_pnl
                if equity_peak > 0:
                    max_drawdown = max(max_drawdown, drawdown / equity_peak * 100)

    # Compute summary stats
    closed = [t for t in trades if t.pnl is not None]
    winning = [t for t in closed if (t.pnl or 0) > 0]
    losing = [t for t in closed if (t.pnl or 0) <= 0]
    hold_days = [t.hold_days for t in closed if t.hold_days is not None]

    total_invested = sum(t.tranche_amount for t in trades if t.action in ('entry', 'addon'))

    return BacktestResult(
        symbol=symbol,
        trades=trades,
        total_trades=len(closed),
        winning_trades=len(winning),
        losing_trades=len(losing),
        win_rate=len(winning) / len(closed) * 100 if closed else 0,
        total_pnl=round(cumulative_pnl, 2),
        total_return_pct=(
            round(cumulative_pnl / total_invested * 100, 2) if total_invested > 0 else 0
        ),
        max_drawdown_pct=round(max_drawdown, 2),
        avg_hold_days=round(sum(hold_days) / len(hold_days), 1) if hold_days else 0,
    )


async def run_backtest_all(
    start_date: date | None = None,
) -> dict[str, BacktestResult]:
    """Run backtest for all active ETFs.

    If start_date is provided, only bars on or after that date are processed.
    """
    symbols = await get_active_symbols()
    params = await load_strategy_params()
    results: dict[str, BacktestResult] = {}

    for symbol in sorted(symbols):
        print(f"Backtesting {symbol}...")
        result = await run_backtest(symbol, params, start_date=start_date)
        results[symbol] = result
        if result.total_trades > 0:
            print(f"  {result.total_trades} trades, "
                  f"win rate {result.win_rate:.0f}%, "
                  f"P&L ₹{result.total_pnl:,.0f} "
                  f"({result.total_return_pct:.1f}%), "
                  f"max DD {result.max_drawdown_pct:.1f}%")

    return results


async def main() -> None:
    """CLI entry point for running backtest."""
    import sys
    if len(sys.argv) > 1:
        symbol = sys.argv[1]
        result = await run_backtest(symbol)
        print(f"\n{symbol}: {result.total_trades} trades, "
              f"win rate {result.win_rate:.0f}%, "
              f"P&L ₹{result.total_pnl:,.0f}")
    else:
        results = await run_backtest_all()
        # Aggregate summary
        total_pnl = sum(r.total_pnl for r in results.values())
        total_trades = sum(r.total_trades for r in results.values())
        winning = sum(r.winning_trades for r in results.values())
        wr = winning / total_trades * 100 if total_trades > 0 else 0
        print("\n=== Aggregate ===")
        print(f"ETFs tested: {len(results)}")
        print(f"Total trades: {total_trades}")
        print(f"Win rate: {wr:.0f}%")
        print(f"Total P&L: ₹{total_pnl:,.0f}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
