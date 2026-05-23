"""New-position entry signal."""

from backend.app.strategy.models import (
    PositionState,
    Signal,
    SignalAction,
    StrategyParams,
    TrendRegime,
)


def check_entry(
    symbol: str,
    trend: TrendRegime,
    pullback: bool,
    position: PositionState | None,
    latest_close: float,
    params: StrategyParams,
) -> Signal | None:
    """Check if a new position entry should be triggered.

    PRD §5.1:
      - No existing position
      - Trend must be STRONG
      - Pullback must be True
      - Buy first tranche at latest_close
    """
    if position is not None and position.is_active:
        return None

    if trend != TrendRegime.STRONG:
        return None

    if not pullback:
        return None

    amount = params.initial_tranche
    return Signal(
        symbol=symbol,
        action=SignalAction.ENTRY,
        tranche_amount=amount,
        limit_price=latest_close,
        reason="Entry tranche 1 — trend Strong, pullback confirmed",
    )
