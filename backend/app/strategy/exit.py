"""Profit-target and time-stop exit signals."""

from datetime import date

from dateutil.relativedelta import relativedelta

from backend.app.strategy.models import (
    PositionState,
    Signal,
    SignalAction,
    StrategyParams,
)


def check_exit(
    symbol: str,
    latest_close: float,
    position: PositionState | None,
    today: date,
    params: StrategyParams,
) -> Signal | None:
    """Check if the position should be exited.

    PRD §5.5:
      - Profit exit: latest_close >= WAC * (1 + profit_target_pct / 100)
      - Time exit:  entered_at + time_stop_months <= today
      - Profit exit takes priority
    """
    if position is None or not position.is_active:
        return None

    # Profit-target exit (checked first, takes priority)
    if position.weighted_avg_cost is not None and position.weighted_avg_cost > 0:
        target_price = position.weighted_avg_cost * (1 + params.profit_target_pct / 100)
        if latest_close >= target_price:
            return Signal(
                symbol=symbol,
                action=SignalAction.EXIT_PROFIT,
                tranche_amount=position.total_capital_deployed,
                limit_price=latest_close,
                reason=(
                    f"Profit exit — close {latest_close:.2f} >= "
                    f"{target_price:.2f} (105% of WAC {position.weighted_avg_cost:.2f})"
                ),
            )

    # Stop-loss exit: close <= WAC * (1 - stop_loss_pct / 100)
    if position.weighted_avg_cost is not None and position.weighted_avg_cost > 0:
        sl_price = position.weighted_avg_cost * (1 - params.stop_loss_pct / 100)
        if latest_close <= sl_price:
            return Signal(
                symbol=symbol,
                action=SignalAction.EXIT_SL,
                tranche_amount=position.total_capital_deployed,
                limit_price=latest_close,
                reason=(
                    f"Stop-loss exit — close {latest_close:.2f} <= "
                    f"{sl_price:.2f} ({100 - params.stop_loss_pct:.0f}% of WAC "
                    f"{position.weighted_avg_cost:.2f})"
                ),
            )

    # Time-stop exit
    if position.entered_at is not None:
        deadline = position.entered_at + relativedelta(months=params.time_stop_months)
        if today >= deadline:
            return Signal(
                symbol=symbol,
                action=SignalAction.EXIT_TIME,
                tranche_amount=position.total_capital_deployed,
                limit_price=latest_close,
                reason=(
                    f"Time exit — {today} >= {deadline} "
                    f"({params.time_stop_months} months from entry {position.entered_at})"
                ),
            )

    return None
