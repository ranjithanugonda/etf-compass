from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from backend.app.strategy.exit import check_exit
from backend.app.strategy.models import (
    PositionState,
    SignalAction,
    StrategyParams,
)


def make_active_position(**overrides: object) -> PositionState:
    defaults: dict[str, object] = {
        "status": "active",
        "tranches_used": 2,
        "total_capital_deployed": 500_000,
        "last_buy_price": 200.0,
        "weighted_avg_cost": 195.0,
        "entered_at": date.today() - timedelta(days=60),
    }
    defaults.update(overrides)
    return PositionState(**defaults)  # type: ignore[arg-type]


def test_profit_exit_triggered() -> None:
    pos = make_active_position(weighted_avg_cost=200.0)
    # target = 200 * 1.05 = 210
    signal = check_exit(
        symbol="NIFTYIETF",
        latest_close=211.0,
        position=pos,
        today=date.today(),
        params=StrategyParams(profit_target_pct=5.0),
    )
    assert signal is not None
    assert signal.action == SignalAction.EXIT_PROFIT


def test_profit_exit_at_exact_target() -> None:
    pos = make_active_position(weighted_avg_cost=200.0)
    signal = check_exit(
        symbol="NIFTYIETF",
        latest_close=210.0,
        position=pos,
        today=date.today(),
        params=StrategyParams(profit_target_pct=5.0),
    )
    assert signal is not None
    assert signal.action == SignalAction.EXIT_PROFIT


def test_profit_exit_not_triggered_below_target() -> None:
    pos = make_active_position(weighted_avg_cost=200.0)
    signal = check_exit(
        symbol="NIFTYIETF",
        latest_close=209.0,
        position=pos,
        today=date.today(),
        params=StrategyParams(profit_target_pct=5.0),
    )
    assert signal is None


def test_time_exit_triggered() -> None:
    entered = date.today() - relativedelta(months=4) - timedelta(days=1)
    pos = make_active_position(
        weighted_avg_cost=200.0,
        entered_at=entered,
    )
    signal = check_exit(
        symbol="NIFTYIETF",
        latest_close=190.0,  # below profit target
        position=pos,
        today=date.today(),
        params=StrategyParams(time_stop_months=4),
    )
    assert signal is not None
    assert signal.action == SignalAction.EXIT_TIME


def test_time_exit_not_triggered_within_window() -> None:
    entered = date.today() - relativedelta(months=3)
    pos = make_active_position(
        weighted_avg_cost=200.0,
        entered_at=entered,
    )
    signal = check_exit(
        symbol="NIFTYIETF",
        latest_close=190.0,
        position=pos,
        today=date.today(),
        params=StrategyParams(time_stop_months=4),
    )
    assert signal is None


def test_profit_exit_takes_priority_over_time() -> None:
    entered = date.today() - relativedelta(months=5)
    pos = make_active_position(
        weighted_avg_cost=200.0,
        entered_at=entered,
    )
    signal = check_exit(
        symbol="NIFTYIETF",
        latest_close=211.0,  # triggers profit exit
        position=pos,
        today=date.today(),
        params=StrategyParams(profit_target_pct=5.0, time_stop_months=4),
    )
    assert signal is not None
    assert signal.action == SignalAction.EXIT_PROFIT


def test_no_exit_no_position() -> None:
    signal = check_exit(
        symbol="NIFTYIETF",
        latest_close=211.0,
        position=None,
        today=date.today(),
        params=StrategyParams(),
    )
    assert signal is None


def test_no_exit_flat_position() -> None:
    signal = check_exit(
        symbol="NIFTYIETF",
        latest_close=211.0,
        position=PositionState(status="flat"),
        today=date.today(),
        params=StrategyParams(),
    )
    assert signal is None


def test_no_exit_no_weighted_avg_cost() -> None:
    pos = make_active_position(weighted_avg_cost=None, entered_at=None)
    signal = check_exit(
        symbol="NIFTYIETF",
        latest_close=500.0,
        position=pos,
        today=date.today(),
        params=StrategyParams(),
    )
    assert signal is None
