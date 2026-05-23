"""Daily EOD scan (16:00 IST): ingest OHLC, scan all ETFs, execute signals.

Now writes wiki pages (etfs, decisions, daily, index) after scanning.
"""

import asyncio
from collections import defaultdict
from datetime import date
from pathlib import Path

from backend.app.broker.paper_broker import PaperBroker
from backend.app.broker.state_loader import (
    get_active_symbols,
    load_ohlc_bars,
    load_position,
    load_strategy_params,
)
from backend.app.db import async_session
from backend.app.ingestion.ohlc_ingest import ingest_update
from backend.app.jobs.wiki_logger import log_signal
from backend.app.strategy.models import Signal, SignalAction
from backend.app.strategy.scanner import scan_etf
from backend.app.wiki.indexer import rebuild_index
from backend.app.wiki.writer import write_daily_summary, write_decision_page, write_etf_page

# ETF metadata cache — loaded once per run
_etf_meta: dict[str, dict[str, object]] = {}


async def _load_etf_metadata() -> dict[str, dict[str, object]]:
    from sqlalchemy import select

    from backend.app.models.etf import ETF

    async with async_session() as session:
        result = await session.execute(select(ETF))
        return {
            row.symbol: {
                "name": row.name,
                "category": row.category.value,
                "amc": row.amc,
                "underlying": row.underlying_exposure,
                "beta": row.beta,
                "atr": row.atr,
            }
            for row in result.scalars().all()
        }


async def run_eod_scan(today: date | None = None) -> dict[str, int]:
    if today is None:
        today = date.today()

    print(f"\n=== EOD SCAN — {today.isoformat()} ===\n")

    # 1. Ingest latest OHLC data
    print("--- OHLC Update ---")
    await ingest_update()

    # 2. Load metadata
    meta = await _load_etf_metadata()
    params = await load_strategy_params()
    print(f"Strategy params loaded (max_position_size=₹{params.max_position_size:,.0f})")

    # 3. Scan all ETFs
    symbols = await get_active_symbols()
    print(f"\nScanning {len(symbols)} active ETFs...\n")

    summary: dict[str, int] = {
        "entries": 0, "addons": 0, "profit_exits": 0, "time_exits": 0, "scanned": 0,
    }
    all_signals: list[Signal] = []
    signals_by_symbol: dict[str, list[Signal]] = defaultdict(list)

    for symbol in symbols:
        bars = await load_ohlc_bars(symbol, lookback_days=60)
        position = await load_position(symbol)
        summary["scanned"] += 1

        if not bars:
            continue

        signals = scan_etf(symbol, bars, position, today, params)
        if not signals:
            continue

        async with async_session() as session:
            for signal in signals:
                await PaperBroker.process_signal(signal, session)
                await session.commit()

                log_signal(today, signal)
                all_signals.append(signal)
                signals_by_symbol[symbol].append(signal)

                if signal.action == SignalAction.ENTRY:
                    summary["entries"] += 1
                elif signal.action == SignalAction.ADDON:
                    summary["addons"] += 1
                elif signal.action == SignalAction.EXIT_PROFIT:
                    summary["profit_exits"] += 1
                elif signal.action == SignalAction.EXIT_TIME:
                    summary["time_exits"] += 1
                elif signal.action == SignalAction.EXIT_SL:
                    summary["time_exits"] += 1  # count SL exits alongside time exits

                print(
                    f"  {symbol}: {signal.action.value.upper()} "
                    f"₹{signal.tranche_amount:,.0f} @ {signal.limit_price:.2f}"
                )

    # 4. Write wiki pages
    print("\n--- Writing Wiki Pages ---")

    # Write per-ETF pages for all scanned ETFs
    for symbol in symbols:
        m = meta.get(symbol, {})
        bars = await load_ohlc_bars(symbol, lookback_days=60)
        position = await load_position(symbol)
        sigs = signals_by_symbol.get(symbol, [])

        # Decision pages only when signals exist
        decisions: list[str] = []
        for sig in sigs:
            dp = write_decision_page(symbol, sig, bars, position)
            decisions.append(dp)
            print(f"  decisions/{Path(dp).name}")

        # ETF page always
        ep = write_etf_page(
            symbol=symbol,
            name=str(m.get("name", symbol)),
            category=str(m.get("category", "")),
            amc=str(m.get("amc", "")),
            underlying=str(m.get("underlying", "")),
            beta=float(m["beta"]) if isinstance(m.get("beta"), (int, float)) else None,  # type: ignore[arg-type]
            atr=float(m["atr"]) if isinstance(m.get("atr"), (int, float)) else None,  # type: ignore[arg-type]
            position=position,
            bars=bars,
            recent_signals=sigs,
            decisions=[Path(d).name.replace(".md", "") for d in decisions],
        )
        print(f"  etfs/{Path(ep).name}")

    # 5. Write daily summary
    ds = write_daily_summary(today, all_signals, summary)
    print(f"  daily/{Path(ds).name}")

    # 6. Rebuild index
    rebuild_index()
    print("  index.md rebuilt")

    # 7. Print summary
    print("\n--- Scan Summary ---")
    print(f"ETFs scanned:  {summary['scanned']}")
    print(f"New entries:   {summary['entries']}")
    print(f"Add-ons:       {summary['addons']}")
    print(f"Profit exits:  {summary['profit_exits']}")
    print(f"Time exits:    {summary['time_exits']}")
    print()

    return summary


async def main() -> None:
    await run_eod_scan()


if __name__ == "__main__":
    asyncio.run(main())
