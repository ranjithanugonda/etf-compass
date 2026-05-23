"""OHLC data endpoint for charting."""

from fastapi import APIRouter, Query

from backend.app.broker.state_loader import load_ohlc_bars

router = APIRouter(prefix="/api/ohlc", tags=["ohlc"])


@router.get("/{symbol}")
async def get_ohlc(symbol: str, days: int = Query(500, le=1000)) -> list[dict[str, object]]:
    """Return OHLC bars for charting as a list of {time, open, high, low, close}."""
    bars = await load_ohlc_bars(symbol, lookback_days=days)
    return [
        {
            "time": bar.date.isoformat(),
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "ema21": bar.ema21,
            "ema60": bar.ema60,
        }
        for bar in bars
    ]
