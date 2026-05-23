import asyncio

import pytest


@pytest.fixture
def sample_etf() -> dict[str, object]:
    return {
        "symbol": "NIFTYIETF",
        "name": "Nifty 50 ETF",
        "category": "indian_index",
        "amc": "ICICI Pru",
        "underlying_exposure": "Nifty 50",
        "beta": 1.0,
        "atr": 5.0,
        "active": True,
    }


@pytest.fixture(scope="session")
def event_loop() -> asyncio.AbstractEventLoop:
    """Session-scoped event loop to avoid asyncpg cross-loop errors."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
