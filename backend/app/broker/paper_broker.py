"""Paper broker — simulates fills and records trades in the database."""

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.position import Position, PositionStatus
from backend.app.models.trade import OrderStatus, Trade, TradeAction
from backend.app.strategy.models import Signal, SignalAction


class PaperBroker:
    """Simulates trade execution. Signals are filled immediately at the limit price."""

    @staticmethod
    async def execute_entry(
        symbol: str,
        signal: Signal,
        session: AsyncSession,
    ) -> Trade:
        result = await session.execute(
            select(Position).where(Position.etf_symbol == symbol)
        )
        pos = result.scalar_one_or_none()

        if pos is not None and pos.status == PositionStatus.ACTIVE:
            raise ValueError(f"Active position already exists for {symbol}")

        price = signal.limit_price
        units = round(signal.tranche_amount / price) if price > 0 else 0

        if pos is None:
            pos = Position(etf_symbol=symbol)
            session.add(pos)

        pos.status = PositionStatus.ACTIVE
        pos.tranches_used = 1
        pos.total_capital_deployed = units * price
        pos.total_units = units
        pos.last_buy_price = price
        pos.weighted_avg_cost = price
        pos.entered_at = date.today()

        trade = Trade(
            position=pos,
            action=TradeAction.ENTRY,
            tranche_number=1,
            quantity=units,
            limit_price=price,
            fill_price=price,
            order_status=OrderStatus.FILLED,
            filled_at=datetime.now(),
        )
        session.add(trade)
        return trade

    @staticmethod
    async def execute_addon(
        symbol: str,
        signal: Signal,
        session: AsyncSession,
    ) -> Trade:
        result = await session.execute(
            select(Position).where(Position.etf_symbol == symbol)
        )
        pos = result.scalar_one_or_none()
        if pos is None or pos.status != PositionStatus.ACTIVE:
            raise ValueError(f"No active position for {symbol}")

        price = signal.limit_price
        units = round(signal.tranche_amount / price) if price > 0 else 0
        old_wac = pos.weighted_avg_cost or price
        old_units = pos.total_units

        pos.total_units += units
        pos.total_capital_deployed += units * price
        pos.weighted_avg_cost = (old_wac * old_units + price * units) / pos.total_units
        pos.last_buy_price = price
        pos.tranches_used += 1

        trade = Trade(
            position_id=pos.id,
            action=TradeAction.ADDON,
            tranche_number=pos.tranches_used,
            quantity=units,
            limit_price=price,
            fill_price=price,
            order_status=OrderStatus.FILLED,
            filled_at=datetime.now(),
        )
        session.add(trade)
        return trade

    @staticmethod
    async def execute_exit(
        symbol: str,
        signal: Signal,
        session: AsyncSession,
    ) -> Trade:
        result = await session.execute(
            select(Position).where(Position.etf_symbol == symbol)
        )
        pos = result.scalar_one_or_none()
        if pos is None or pos.status != PositionStatus.ACTIVE:
            raise ValueError(f"No active position for {symbol}")

        action = TradeAction(signal.action.value)

        pos.status = PositionStatus.FLAT
        pos.exited_at = date.today()

        trade = Trade(
            position_id=pos.id,
            action=action,
            tranche_number=pos.tranches_used,
            quantity=int(pos.total_units),
            limit_price=signal.limit_price,
            fill_price=signal.limit_price,
            order_status=OrderStatus.FILLED,
            filled_at=datetime.now(),
        )
        session.add(trade)
        return trade

    @staticmethod
    async def process_signal(signal: Signal, session: AsyncSession) -> Trade:
        if signal.action == SignalAction.ENTRY:
            return await PaperBroker.execute_entry(signal.symbol, signal, session)
        elif signal.action == SignalAction.ADDON:
            return await PaperBroker.execute_addon(signal.symbol, signal, session)
        elif signal.action in (
            SignalAction.EXIT_PROFIT, SignalAction.EXIT_TIME, SignalAction.EXIT_SL
        ):
            return await PaperBroker.execute_exit(signal.symbol, signal, session)
        else:
            raise ValueError(f"Unknown signal action: {signal.action}")
