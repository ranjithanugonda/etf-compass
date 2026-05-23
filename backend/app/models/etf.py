import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db import Base


class ETFCategory(enum.StrEnum):
    COMMODITIES = "commodities"
    SECTORAL = "sectoral"
    INDIAN_INDEX = "indian_index"
    INTERNATIONAL = "international"


class ETF(Base):
    __tablename__ = "etf"

    symbol: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[ETFCategory] = mapped_column(nullable=False)
    amc: Mapped[str] = mapped_column(String(100), nullable=False)
    underlying_exposure: Mapped[str] = mapped_column(Text, nullable=False)
    beta: Mapped[float | None] = mapped_column(Float, nullable=True)
    atr: Mapped[float | None] = mapped_column(Float, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    added_date: Mapped[date] = mapped_column(Date, default=datetime.now, nullable=False)
