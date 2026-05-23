"""Pydantic response models for position endpoints."""

from datetime import date

from pydantic import BaseModel


class PositionResponse(BaseModel):
    symbol: str
    name: str
    category: str
    status: str
    tranches_used: int
    total_capital_deployed: float
    total_units: float
    last_buy_price: float | None
    weighted_avg_cost: float | None
    unrealized_pnl: float | None
    trend_regime: str | None
    entered_at: date | None
    days_held: int | None
