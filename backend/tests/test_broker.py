"""Tests for paper_broker — signal execution and position updates."""

import pytest
from sqlalchemy import text

from backend.app.broker.paper_broker import PaperBroker
from backend.app.db import async_session
from backend.app.strategy.models import Signal, SignalAction


async def _cleanup(symbol: str) -> None:
    async with async_session() as s:
        await s.execute(
            text("DELETE FROM trade WHERE position_id IN "
                 "(SELECT id FROM position WHERE etf_symbol = :sym)"),
            {"sym": symbol},
        )
        await s.execute(
            text("DELETE FROM position WHERE etf_symbol = :sym"),
            {"sym": symbol},
        )
        await s.commit()


@pytest.mark.asyncio
async def test_entry_persists_position() -> None:
    symbol = "NIFTYIETF"
    await _cleanup(symbol)

    signal = Signal(
        symbol=symbol, action=SignalAction.ENTRY,
        tranche_amount=300_000, limit_price=200.0, reason="test",
    )
    async with async_session() as s:
        trade = await PaperBroker.execute_entry(symbol, signal, s)
        await s.commit()

    assert trade.action.value == "entry"
    assert trade.fill_price == 200.0

    await _cleanup(symbol)


@pytest.mark.asyncio
async def test_addon_updates_wac() -> None:
    symbol = "BANKBEES"
    await _cleanup(symbol)

    entry = Signal(
        symbol=symbol, action=SignalAction.ENTRY,
        tranche_amount=300_000, limit_price=200.0, reason="test",
    )
    async with async_session() as s:
        await PaperBroker.execute_entry(symbol, entry, s)
        await s.commit()

    addon = Signal(
        symbol=symbol, action=SignalAction.ADDON,
        tranche_amount=100_000, limit_price=190.0, reason="test",
    )
    async with async_session() as s:
        trade = await PaperBroker.execute_addon(symbol, addon, s)
        await s.commit()

    assert trade.action.value == "addon"

    await _cleanup(symbol)


@pytest.mark.asyncio
async def test_exit_flattens_position() -> None:
    symbol = "ITBEES"
    await _cleanup(symbol)

    entry = Signal(
        symbol=symbol, action=SignalAction.ENTRY,
        tranche_amount=300_000, limit_price=200.0, reason="test",
    )
    async with async_session() as s:
        await PaperBroker.execute_entry(symbol, entry, s)
        await s.commit()

    exit_sig = Signal(
        symbol=symbol, action=SignalAction.EXIT_PROFIT,
        tranche_amount=300_000, limit_price=210.0, reason="test",
    )
    async with async_session() as s:
        trade = await PaperBroker.execute_exit(symbol, exit_sig, s)
        await s.commit()

    assert trade.action.value == "exit_profit"

    await _cleanup(symbol)


@pytest.mark.asyncio
async def test_process_signal_dispatches() -> None:
    symbol = "MAFANG"
    await _cleanup(symbol)

    signal = Signal(
        symbol=symbol, action=SignalAction.ENTRY,
        tranche_amount=300_000, limit_price=200.0, reason="test",
    )
    async with async_session() as s:
        trade = await PaperBroker.process_signal(signal, s)
        await s.commit()

    assert trade.action.value == "entry"

    await _cleanup(symbol)
