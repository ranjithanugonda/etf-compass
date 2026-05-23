from datetime import date, timedelta

from backend.app.strategy.addon import check_addon
from backend.app.strategy.models import (
    PositionState,
    SignalAction,
    StrategyParams,
    TrendRegime,
)


def make_active_position(**overrides: object) -> PositionState:
    defaults: dict[str, object] = {
        "status": "active",
        "tranches_used": 1,
        "total_capital_deployed": 300_000,
        "last_buy_price": 200.0,
        "weighted_avg_cost": 200.0,
        "entered_at": date.today() - timedelta(days=30),
    }
    defaults.update(overrides)
    return PositionState(**defaults)  # type: ignore[arg-type]


def test_addon_triggered() -> None:
    pos = make_active_position()
    # LBP=200, threshold = 200*0.975 = 195
    signal = check_addon(
        symbol="NIFTYIETF",
        latest_close=194.0,
        position=pos,
        trend=TrendRegime.STRONG,
        today=date.today(),
        params=StrategyParams(),
    )
    assert signal is not None
    assert signal.action == SignalAction.ADDON
    assert signal.tranche_amount == 200_000  # second_tranche


def test_addon_not_triggered_price_above_threshold() -> None:
    pos = make_active_position()
    signal = check_addon(
        symbol="NIFTYIETF",
        latest_close=196.0,  # > 195
        position=pos,
        trend=TrendRegime.STRONG,
        today=date.today(),
        params=StrategyParams(),
    )
    assert signal is None


def test_addon_not_triggered_no_position() -> None:
    signal = check_addon(
        symbol="NIFTYIETF",
        latest_close=194.0,
        position=None,
        trend=TrendRegime.STRONG,
        today=date.today(),
        params=StrategyParams(),
    )
    assert signal is None


def test_addon_not_triggered_flat_position() -> None:
    pos = PositionState(status="flat")
    signal = check_addon(
        symbol="NIFTYIETF",
        latest_close=194.0,
        position=pos,
        trend=TrendRegime.STRONG,
        today=date.today(),
        params=StrategyParams(),
    )
    assert signal is None


def test_addon_not_triggered_weak_trend() -> None:
    pos = make_active_position()
    signal = check_addon(
        symbol="NIFTYIETF",
        latest_close=194.0,
        position=pos,
        trend=TrendRegime.WEAK,
        today=date.today(),
        params=StrategyParams(),
    )
    assert signal is None


def test_neutral_trend_half_allocation() -> None:
    pos = make_active_position()
    signal = check_addon(
        symbol="NIFTYIETF",
        latest_close=194.0,
        position=pos,
        trend=TrendRegime.NEUTRAL,
        today=date.today(),
        params=StrategyParams(),
    )
    assert signal is not None
    assert signal.tranche_amount == 100_000  # half of second_tranche (200K)


def test_max_tranches_reached() -> None:
    pos = make_active_position(tranches_used=9)
    signal = check_addon(
        symbol="NIFTYIETF",
        latest_close=194.0,
        position=pos,
        trend=TrendRegime.STRONG,
        today=date.today(),
        params=StrategyParams(),
    )
    assert signal is None


def test_would_exceed_max_position_size() -> None:
    pos = make_active_position(total_capital_deployed=1_200_000)
    signal = check_addon(
        symbol="NIFTYIETF",
        latest_close=194.0,
        position=pos,
        trend=TrendRegime.STRONG,
        today=date.today(),
        params=StrategyParams(),
    )
    assert signal is None


def test_addon_window_expired() -> None:
    pos = make_active_position(last_addon_date=date.today() - timedelta(days=10))
    signal = check_addon(
        symbol="NIFTYIETF",
        latest_close=194.0,
        position=pos,
        trend=TrendRegime.STRONG,
        today=date.today(),
        params=StrategyParams(addon_duration_days=7),
    )
    assert signal is None


def test_addon_window_open() -> None:
    pos = make_active_position(last_addon_date=date.today() - timedelta(days=3))
    signal = check_addon(
        symbol="NIFTYIETF",
        latest_close=194.0,
        position=pos,
        trend=TrendRegime.STRONG,
        today=date.today(),
        params=StrategyParams(addon_duration_days=7),
    )
    assert signal is not None


def test_addon_no_prior_addon_window_not_checked() -> None:
    pos = make_active_position(last_addon_date=None)
    signal = check_addon(
        symbol="NIFTYIETF",
        latest_close=194.0,
        position=pos,
        trend=TrendRegime.STRONG,
        today=date.today(),
        params=StrategyParams(),
    )
    assert signal is not None


def test_addon_no_last_buy_price() -> None:
    pos = make_active_position(last_buy_price=None)
    signal = check_addon(
        symbol="NIFTYIETF",
        latest_close=194.0,
        position=pos,
        trend=TrendRegime.STRONG,
        today=date.today(),
        params=StrategyParams(),
    )
    assert signal is None
