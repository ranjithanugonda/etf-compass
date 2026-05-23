"""Pydantic response models for trade endpoints."""

from datetime import datetime

from pydantic import BaseModel


class TradeResponse(BaseModel):
    id: int
    symbol: str
    action: str
    tranche_number: int
    quantity: int
    limit_price: float
    fill_price: float | None
    order_status: str
    order_placed_at: datetime
    filled_at: datetime | None
