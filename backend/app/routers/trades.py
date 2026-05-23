"""Trade history endpoints — public read + manual placement."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select

from backend.app.db import async_session
from backend.app.models.position import Position, PositionStatus
from backend.app.models.trade import OrderStatus, Trade, TradeAction
from backend.app.schemas.trades import TradeResponse

router = APIRouter(prefix="/api/trades", tags=["trades"])


class PlaceTradeRequest(BaseModel):
    symbol: str
    action: str  # entry, addon, exit_profit, exit_time
    quantity: int
    limit_price: float


async def _trade_to_response(trade: Trade) -> TradeResponse:
    # Look up symbol from position
    symbol = ""
    async with async_session() as s:
        r = await s.execute(select(Position).where(Position.id == trade.position_id))
        pos = r.scalar_one_or_none()
        if pos:
            symbol = pos.etf_symbol

    return TradeResponse(
        id=trade.id,
        symbol=symbol,
        action=trade.action.value,
        tranche_number=trade.tranche_number,
        quantity=trade.quantity,
        limit_price=trade.limit_price,
        fill_price=trade.fill_price,
        order_status=trade.order_status.value,
        order_placed_at=trade.order_placed_at,
        filled_at=trade.filled_at,
    )


@router.get("", response_model=list[TradeResponse])
async def list_trades(
    symbol: str | None = Query(None),
    action: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
) -> list[TradeResponse]:
    async with async_session() as session:
        query = select(Trade)

        if symbol:
            # Join with position to filter by symbol
            subq = select(Position.id).where(Position.etf_symbol == symbol).scalar_subquery()
            query = query.where(Trade.position_id.in_(subq))

        if action:
            from backend.app.models.trade import TradeAction
            try:
                trade_action = TradeAction(action)
                query = query.where(Trade.action == trade_action)
            except ValueError:
                pass

        query = query.order_by(Trade.filled_at.desc().nullslast()).offset(offset).limit(limit)
        result = await session.execute(query)
        trades = result.scalars().all()

    responses = []
    for t in trades:
        responses.append(await _trade_to_response(t))
    return responses


@router.get("/recent", response_model=list[TradeResponse])
async def recent_trades() -> list[TradeResponse]:
    async with async_session() as session:
        result = await session.execute(
            select(Trade).order_by(Trade.filled_at.desc().nullslast()).limit(20)
        )
        trades = result.scalars().all()

    responses = []
    for t in trades:
        responses.append(await _trade_to_response(t))
    return responses


@router.post("/place", response_model=TradeResponse)
async def place_trade(body: PlaceTradeRequest) -> TradeResponse:
    """Manually place a paper trade. Accepts symbol, action, quantity, limit_price."""
    try:
        trade_action = TradeAction(body.action)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid action: {body.action}. "
                f"Must be entry, addon, exit_profit, or exit_time."
            ),
        )

    async with async_session() as session:
        result = await session.execute(
            select(Position).where(Position.etf_symbol == body.symbol)
        )
        pos = result.scalar_one_or_none()

        if trade_action == TradeAction.ENTRY:
            if pos is not None and pos.status == PositionStatus.ACTIVE:
                raise HTTPException(
                    status_code=400,
                    detail=f"Active position already exists for {body.symbol}",
                )
            if pos is None:
                pos = Position(etf_symbol=body.symbol)
                session.add(pos)

            pos.status = PositionStatus.ACTIVE
            pos.tranches_used = 1
            pos.total_capital_deployed = body.quantity * body.limit_price
            pos.total_units = body.quantity
            pos.last_buy_price = body.limit_price
            pos.weighted_avg_cost = body.limit_price
            pos.entered_at = datetime.now().date()

            trade = Trade(
                position=pos,
                action=TradeAction.ENTRY,
                tranche_number=1,
                quantity=body.quantity,
                limit_price=body.limit_price,
                fill_price=body.limit_price,
                order_status=OrderStatus.FILLED,
                filled_at=datetime.now(),
            )

        elif trade_action == TradeAction.ADDON:
            if pos is None or pos.status != PositionStatus.ACTIVE:
                raise HTTPException(
                    status_code=400,
                    detail=f"No active position for {body.symbol}",
                )

            old_wac = pos.weighted_avg_cost or body.limit_price
            old_units = pos.total_units
            pos.total_units += body.quantity
            pos.total_capital_deployed += body.quantity * body.limit_price
            pos.weighted_avg_cost = (
                (old_wac * old_units + body.limit_price * body.quantity) / pos.total_units
            )
            pos.last_buy_price = body.limit_price
            pos.tranches_used += 1

            trade = Trade(
                position_id=pos.id,
                action=TradeAction.ADDON,
                tranche_number=pos.tranches_used,
                quantity=body.quantity,
                limit_price=body.limit_price,
                fill_price=body.limit_price,
                order_status=OrderStatus.FILLED,
                filled_at=datetime.now(),
            )

        else:  # EXIT_PROFIT or EXIT_TIME
            if pos is None or pos.status != PositionStatus.ACTIVE:
                raise HTTPException(
                    status_code=400,
                    detail=f"No active position for {body.symbol}",
                )

            pos.status = PositionStatus.FLAT
            pos.exited_at = datetime.now().date()

            trade = Trade(
                position_id=pos.id,
                action=trade_action,
                tranche_number=pos.tranches_used,
                quantity=body.quantity,
                limit_price=body.limit_price,
                fill_price=body.limit_price,
                order_status=OrderStatus.FILLED,
                filled_at=datetime.now(),
            )

        session.add(trade)
        await session.commit()
        await session.refresh(trade)

        return TradeResponse(
            id=trade.id,
            symbol=body.symbol,
            action=trade.action.value,
            tranche_number=trade.tranche_number,
            quantity=trade.quantity,
            limit_price=trade.limit_price,
            fill_price=trade.fill_price,
            order_status=trade.order_status.value,
            order_placed_at=trade.order_placed_at,
            filled_at=trade.filled_at,
        )
