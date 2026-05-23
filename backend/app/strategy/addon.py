"""Additional-tranche (DCA) signal."""

from datetime import date, timedelta

from backend.app.strategy.allocator import get_tranche_amount
from backend.app.strategy.models import (
    PositionState,
    Signal,
    SignalAction,
    StrategyParams,
    TrendRegime,
)


def check_addon(
    symbol: str,
    latest_close: float,
    position: PositionState | None,
    trend: TrendRegime,
    today: date,
    params: StrategyParams,
) -> Signal | None:
    """Check if an additional tranche should be triggered.

    PRD §5.4:
      - Must have an ACTIVE position
      - latest_close <= LBP * (1 - addon_threshold_pct / 100)
      - Max tranches not reached
      - Total deployed after addon <= max_position_size
      - WEAK trend: no add-ons allowed
      - NEUTRAL trend: add-on at 50% allocation (PRD §5.2)
      - Add-on window: within addon_duration_days of last addon
    """
    if position is None or not position.is_active:
        return None

    if trend == TrendRegime.WEAK:
        return None

    if position.tranches_used >= params.max_tranches:
        return None

    if position.last_buy_price is None:
        return None

    threshold_price = position.last_buy_price * (1 - params.addon_threshold_pct / 100)
    if latest_close > threshold_price:
        return None

    next_tranche = position.tranches_used + 1
    amount = get_tranche_amount(next_tranche, params)

    if position.total_capital_deployed + amount > params.max_position_size:
        return None

    if position.last_addon_date is not None:
        window_end = position.last_addon_date + timedelta(days=params.addon_duration_days)
        if today > window_end:
            return None

    if trend == TrendRegime.NEUTRAL:
        amount = amount * 0.5

    return Signal(
        symbol=symbol,
        action=SignalAction.ADDON,
        tranche_amount=amount,
        limit_price=latest_close,
        reason=(
            f"Addon tranche {next_tranche} — "
            f"price {latest_close:.2f} <= {threshold_price:.2f} "
            f"(97.5% of LBP {position.last_buy_price:.2f})"
        ),
    )
