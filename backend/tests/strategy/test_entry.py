from backend.app.strategy.entry import check_entry
from backend.app.strategy.models import (
    PositionState,
    SignalAction,
    StrategyParams,
    TrendRegime,
)


def test_entry_when_all_conditions_met() -> None:
    signal = check_entry(
        symbol="NIFTYIETF",
        trend=TrendRegime.STRONG,
        pullback=True,
        position=None,
        latest_close=200.0,
        params=StrategyParams(),
    )
    assert signal is not None
    assert signal.action == SignalAction.ENTRY
    assert signal.tranche_amount == 300_000
    assert signal.limit_price == 200.0


def test_no_entry_when_already_active() -> None:
    pos = PositionState(status="active", tranches_used=1, total_capital_deployed=300_000)
    signal = check_entry(
        symbol="NIFTYIETF",
        trend=TrendRegime.STRONG,
        pullback=True,
        position=pos,
        latest_close=200.0,
        params=StrategyParams(),
    )
    assert signal is None


def test_no_entry_when_neutral_trend() -> None:
    signal = check_entry(
        symbol="NIFTYIETF",
        trend=TrendRegime.NEUTRAL,
        pullback=True,
        position=None,
        latest_close=200.0,
        params=StrategyParams(),
    )
    assert signal is None


def test_no_entry_when_weak_trend() -> None:
    signal = check_entry(
        symbol="NIFTYIETF",
        trend=TrendRegime.WEAK,
        pullback=True,
        position=None,
        latest_close=200.0,
        params=StrategyParams(),
    )
    assert signal is None


def test_no_entry_without_pullback() -> None:
    signal = check_entry(
        symbol="NIFTYIETF",
        trend=TrendRegime.STRONG,
        pullback=False,
        position=None,
        latest_close=200.0,
        params=StrategyParams(),
    )
    assert signal is None


def test_entry_with_flat_position() -> None:
    pos = PositionState(status="flat")
    signal = check_entry(
        symbol="NIFTYIETF",
        trend=TrendRegime.STRONG,
        pullback=True,
        position=pos,
        latest_close=200.0,
        params=StrategyParams(),
    )
    assert signal is not None
    assert signal.action == SignalAction.ENTRY
