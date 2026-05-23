from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db import Base

if TYPE_CHECKING:
    from backend.app.models.position import Position


class TradeAction(enum.StrEnum):
    ENTRY = "entry"
    ADDON = "addon"
    EXIT_PROFIT = "exit_profit"
    EXIT_TIME = "exit_time"
    EXIT_SL = "exit_sl"


class OrderStatus(enum.StrEnum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"


class Trade(Base):
    __tablename__ = "trade"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    position_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("position.id"), nullable=False, index=True
    )
    action: Mapped[TradeAction] = mapped_column(nullable=False)
    tranche_number: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    limit_price: Mapped[float] = mapped_column(Float, nullable=False)
    fill_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    order_status: Mapped[OrderStatus] = mapped_column(
        default=OrderStatus.PENDING, nullable=False
    )
    order_placed_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )
    filled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

    position: Mapped[Position] = relationship(back_populates="trades")
