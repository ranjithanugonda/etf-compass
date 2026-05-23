from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from backend.app.strategy.models import (
    OHLCBar,
    PositionState,
    SignalAction,
    StrategyParams,
)
from backend.app.strategy.scanner import scan_etf


def make_bars(closes: list[float]) -> list[OHLCBar]:
    """Create bars with close > EMA21 > EMA60 (Strong trend by default)."""
    today = date.today()
    bars: list[OHLCBar] = []
    for i, c in enumerate(closes):
        d = today - timedelta(days=len(closes) - 1 - i)
        bars.append(OHLCBar(
            date=d, open=c, high=c, low=c, close=c, volume=1000,
            ema21=c - 1, ema60=c - 2,
        ))
    return bars


def test_empty_bars() -> None:
    assert scan_etf("X", [], None, date.today(), StrategyParams()) == []


def test_entry_signal_generated() -> None:
    # 5 bars with a pullback: high=105, last=102 (decline 2.86%)
    bars = make_bars([100.0, 105.0, 104.0, 103.0, 102.0])
    signals = scan_etf("NIFTYIETF", bars, None, date.today(), StrategyParams())
    assert len(signals) == 1
    assert signals[0].action == SignalAction.ENTRY


def test_exit_blocks_entry() -> None:
    entered = date.today() - relativedelta(months=5)
    pos = PositionState(
        status="active",
        tranches_used=1,
        total_capital_deployed=300_000,
        weighted_avg_cost=100.0,
        entered_at=entered,
    )
    bars = make_bars([100.0, 105.0, 104.0, 103.0, 102.0])
    signals = scan_etf("NIFTYIETF", bars, pos, date.today(), StrategyParams())
    assert len(signals) == 1
    assert signals[0].action == SignalAction.EXIT_TIME


def test_no_entry_without_pullback() -> None:
    # Flat prices, no pullback
    bars = make_bars([100.0] * 30)
    signals = scan_etf("NIFTYIETF", bars, None, date.today(), StrategyParams())
    assert signals == []


def test_addon_signal_generated() -> None:
    pos = PositionState(
        status="active",
        tranches_used=1,
        total_capital_deployed=300_000,
        last_buy_price=200.0,
        weighted_avg_cost=200.0,
        entered_at=date.today() - timedelta(days=30),
    )
    # Price below 97.5% of LBP (195), but no pullback so no entry
    bars = make_bars([195.0] * 30)
    signals = scan_etf("NIFTYIETF", bars, pos, date.today(), StrategyParams())
    assert len(signals) == 1
    assert signals[0].action == SignalAction.ADDON
