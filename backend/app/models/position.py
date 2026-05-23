from __future__ import annotations

import enum
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db import Base

if TYPE_CHECKING:
    from backend.app.models.trade import Trade


class PositionStatus(enum.StrEnum):
    ACTIVE = "active"
    FLAT = "flat"


class TrendRegime(enum.StrEnum):
    STRONG = "strong"
    NEUTRAL = "neutral"
    WEAK = "weak"


class Position(Base):
    __tablename__ = "position"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    etf_symbol: Mapped[str] = mapped_column(
        String(20), ForeignKey("etf.symbol"), nullable=False, unique=True
    )
    status: Mapped[PositionStatus] = mapped_column(default=PositionStatus.FLAT, nullable=False)
    total_capital_deployed: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_units: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tranches_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_buy_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    weighted_avg_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    unrealized_pnl: Mapped[float | None] = mapped_column(Float, nullable=True)
    trend_regime: Mapped[TrendRegime | None] = mapped_column(nullable=True)
    entered_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    exited_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    trades: Mapped[list[Trade]] = relationship(back_populates="position")
