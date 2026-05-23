"""Load DB rows and convert to pure strategy dataclasses."""


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db import async_session
from backend.app.models.etf import ETF
from backend.app.models.ohlc import OHLC
from backend.app.models.position import Position, PositionStatus
from backend.app.models.strategy_params import StrategyParam
from backend.app.strategy.models import OHLCBar, PositionState, StrategyParams


async def get_active_symbols(session: AsyncSession | None = None) -> list[str]:
    if session is None:
        async with async_session() as s:
            return await _get_active_symbols(s)
    return await _get_active_symbols(session)


async def _get_active_symbols(session: AsyncSession) -> list[str]:
    result = await session.execute(select(ETF.symbol).where(ETF.active.is_(True)))
    return [row[0] for row in result.fetchall()]


async def load_strategy_params(session: AsyncSession | None = None) -> StrategyParams:
    if session is None:
        async with async_session() as s:
            return await _load_strategy_params(s)
    return await _load_strategy_params(session)


async def _load_strategy_params(session: AsyncSession) -> StrategyParams:
    result = await session.execute(select(StrategyParam))
    rows = result.scalars().all()

    kwargs: dict[str, object] = {}
    type_map: dict[str, type] = {
        "total_corpus": float,
        "initial_tranche": float,
        "second_tranche": float,
        "third_tranche": float,
        "addon_tranche": float,
        "max_position_size": float,
        "max_tranches": int,
        "profit_target_pct": float,
        "stop_loss_pct": float,
        "time_stop_months": int,
        "addon_threshold_pct": float,
        "addon_duration_days": int,
        "pullback_weekly_pct": float,
        "pullback_weekly_days": int,
        "pullback_monthly_pct": float,
        "pullback_monthly_days": int,
    }

    for row in rows:
        if row.param_name in type_map:
            kwargs[row.param_name] = type_map[row.param_name](row.param_value)

    return StrategyParams(**kwargs)  # type: ignore[arg-type]


async def load_ohlc_bars(
    symbol: str, lookback_days: int = 60, session: AsyncSession | None = None,
) -> list[OHLCBar]:
    if session is None:
        async with async_session() as s:
            return await _load_ohlc_bars(symbol, lookback_days, s)
    return await _load_ohlc_bars(symbol, lookback_days, session)


async def _load_ohlc_bars(
    symbol: str, lookback_days: int, session: AsyncSession,
) -> list[OHLCBar]:
    result = await session.execute(
        select(OHLC)
        .where(OHLC.symbol == symbol)
        .order_by(OHLC.date.asc())
        .limit(lookback_days)
    )
    rows = result.scalars().all()

    return [
        OHLCBar(
            date=r.date,
            open=r.open,
            high=r.high,
            low=r.low,
            close=r.close,
            volume=r.volume,
            ema21=r.ema21,
            ema60=r.ema60,
        )
        for r in rows
    ]


async def load_position(
    symbol: str, session: AsyncSession | None = None,
) -> PositionState | None:
    if session is None:
        async with async_session() as s:
            return await _load_position(symbol, s)
    return await _load_position(symbol, session)


async def _load_position(
    symbol: str, session: AsyncSession,
) -> PositionState | None:
    result = await session.execute(
        select(Position).where(Position.etf_symbol == symbol)
    )
    pos = result.scalar_one_or_none()

    if pos is None:
        return None

    return PositionState(
        status="active" if pos.status == PositionStatus.ACTIVE else "flat",
        tranches_used=pos.tranches_used,
        total_capital_deployed=pos.total_capital_deployed,
        total_units=pos.total_units,
        last_buy_price=pos.last_buy_price,
        weighted_avg_cost=pos.weighted_avg_cost,
        entered_at=pos.entered_at,
        last_addon_date=None,
    )
