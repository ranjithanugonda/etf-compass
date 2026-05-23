"""Tests for state_loader — DB to strategy dataclass conversion."""

import pytest

from backend.app.broker.state_loader import (
    get_active_symbols,
    load_ohlc_bars,
    load_strategy_params,
)


@pytest.mark.asyncio
async def test_get_active_symbols() -> None:
    symbols = await get_active_symbols()
    assert len(symbols) == 21
    assert "NIFTYIETF" in symbols


@pytest.mark.asyncio
async def test_load_strategy_params() -> None:
    params = await load_strategy_params()
    assert params.total_corpus == 15_000_000


@pytest.mark.asyncio
async def test_load_ohlc_bars_returns_data() -> None:
    bars = await load_ohlc_bars("NIFTYIETF", lookback_days=5)
    assert isinstance(bars, list)
    assert len(bars) > 0
