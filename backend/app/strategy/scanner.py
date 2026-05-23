"""EOD scanner — orchestrates all strategy checks for one ETF."""

from datetime import date

from backend.app.strategy.addon import check_addon
from backend.app.strategy.entry import check_entry
from backend.app.strategy.exit import check_exit
from backend.app.strategy.models import (
    OHLCBar,
    PositionState,
    Signal,
    StrategyParams,
)
from backend.app.strategy.pullback import detect_pullback
from backend.app.strategy.trend import determine_trend


def scan_etf(
    symbol: str,
    bars: list[OHLCBar],
    position: PositionState | None,
    today: date,
    params: StrategyParams,
) -> list[Signal]:
    """Run all strategy checks for one ETF and return ordered signals.

    Order: exit signals first (if a time exit fires, we skip entry/addon),
    then entry, then addon.
    """
    if not bars:
        return []

    latest = bars[-1]
    trend = determine_trend(latest.close, latest.ema21, latest.ema60)
    signals: list[Signal] = []

    # Exit checks first — if we need to exit, don't generate entry/addon
    exit_signal = check_exit(symbol, latest.close, position, today, params)
    if exit_signal is not None:
        signals.append(exit_signal)
        return signals

    # Pullback detection (needed for entry)
    pullback = detect_pullback(
        bars,
        weekly_pct=params.pullback_weekly_pct,
        weekly_days=params.pullback_weekly_days,
        monthly_pct=params.pullback_monthly_pct,
        monthly_days=params.pullback_monthly_days,
    )

    # Entry check
    entry_signal = check_entry(symbol, trend, pullback, position, latest.close, params)
    if entry_signal is not None:
        signals.append(entry_signal)
        return signals

    # Addon check (only if no entry was generated)
    addon_signal = check_addon(symbol, latest.close, position, trend, today, params)
    if addon_signal is not None:
        signals.append(addon_signal)

    return signals
