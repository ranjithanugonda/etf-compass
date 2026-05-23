"""Position endpoints — public read."""

from datetime import date

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from backend.app.db import async_session
from backend.app.models.ohlc import OHLC
from backend.app.models.position import Position, PositionStatus
from backend.app.schemas.positions import PositionResponse

router = APIRouter(prefix="/api/positions", tags=["positions"])


@router.get("", response_model=list[PositionResponse])
async def list_positions() -> list[PositionResponse]:
    async with async_session() as session:
        result = await session.execute(
            select(Position).options(joinedload(Position.trades))
        )
        positions = result.unique().scalars().all()

    out: list[PositionResponse] = []
    for pos in positions:
        # Get latest close for unrealized P&L
        latest_close = None
        async with async_session() as s2:
            r = await s2.execute(
                select(OHLC.close).where(OHLC.symbol == pos.etf_symbol).order_by(
                    OHLC.date.desc()
                ).limit(1)
            )
            row = r.first()
            if row:
                latest_close = row[0]

        unrealized = None
        if pos.status == PositionStatus.ACTIVE and latest_close and pos.weighted_avg_cost:
            unrealized = (latest_close - pos.weighted_avg_cost) * pos.total_units

        days_held = None
        if pos.entered_at:
            days_held = (date.today() - pos.entered_at).days

        out.append(PositionResponse(
            symbol=pos.etf_symbol,
            name=pos.etf_symbol,  # will join with ETF table
            category="",
            status=pos.status.value,
            tranches_used=pos.tranches_used,
            total_capital_deployed=pos.total_capital_deployed,
            total_units=pos.total_units,
            last_buy_price=pos.last_buy_price,
            weighted_avg_cost=pos.weighted_avg_cost,
            unrealized_pnl=round(unrealized, 2) if unrealized else None,
            trend_regime=None,
            entered_at=pos.entered_at,
            days_held=days_held,
        ))

    return out


@router.get("/{symbol}", response_model=PositionResponse)
async def get_position(symbol: str) -> PositionResponse:
    async with async_session() as session:
        result = await session.execute(
            select(Position).where(Position.etf_symbol == symbol).options(
                joinedload(Position.trades)
            )
        )
        pos = result.unique().scalar_one_or_none()

    if pos is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"No position for {symbol}")

    latest_close = None
    async with async_session() as s2:
        r = await s2.execute(
            select(OHLC.close).where(OHLC.symbol == symbol).order_by(
                OHLC.date.desc()
            ).limit(1)
        )
        row = r.first()
        if row:
            latest_close = row[0]

    unrealized = None
    if pos.status == PositionStatus.ACTIVE and latest_close and pos.weighted_avg_cost:
        unrealized = (latest_close - pos.weighted_avg_cost) * pos.total_units

    days_held = None
    if pos.entered_at:
        days_held = (date.today() - pos.entered_at).days

    return PositionResponse(
        symbol=pos.etf_symbol,
        name=pos.etf_symbol,
        category="",
        status=pos.status.value,
        tranches_used=pos.tranches_used,
        total_capital_deployed=pos.total_capital_deployed,
        total_units=pos.total_units,
        last_buy_price=pos.last_buy_price,
        weighted_avg_cost=pos.weighted_avg_cost,
        unrealized_pnl=round(unrealized, 2) if unrealized else None,
        trend_regime=None,
        entered_at=pos.entered_at,
        days_held=days_held,
    )
