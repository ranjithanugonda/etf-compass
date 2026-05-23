"""Download OHLC data from yfinance, compute EMAs, store to parquet and Postgres.

Modes:
    backfill: pull ~2 years of history for all ETFs (initial setup)
    update:   pull latest data only (daily EOD job)
"""

import asyncio
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.app.db import async_session
from backend.app.models.etf import ETF
from backend.app.models.ohlc import OHLC

DATA_DIR = Path("data/ohlc")
DATA_DIR.mkdir(parents=True, exist_ok=True)

YF_SYMBOL_SUFFIX = ".NS"  # NSE suffix for yfinance


def _with_suffix(symbol: str) -> str:
    return f"{symbol}{YF_SYMBOL_SUFFIX}"


async def get_active_symbols() -> list[str]:
    async with async_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(ETF.symbol).where(ETF.active.is_(True)))
        return [row[0] for row in result.fetchall()]


async def get_last_date(symbol: str) -> date | None:
    """Return the most recent date in the DB for this symbol, or None."""
    async with async_session() as session:
        from sqlalchemy import desc, select
        result = await session.execute(
            select(OHLC.date).where(OHLC.symbol == symbol).order_by(desc(OHLC.date)).limit(1)
        )
        row = result.first()
        return row[0] if row else None


def download_and_compute(symbol: str, start_date: date | None = None) -> pd.DataFrame:
    """Download OHLC from yfinance and compute EMA21, EMA60.

    If start_date is None, defaults to 2 years back.
    Returns a DataFrame with columns matching the OHLC table.
    """
    ticker = yf.Ticker(_with_suffix(symbol))
    if start_date is None:
        start_date = date.today() - timedelta(days=730)

    df = ticker.history(start=start_date.isoformat(), interval="1d")

    if df.empty:
        print(f"  {symbol}: no data from yfinance (start={start_date})")
        return df

    df.index = pd.to_datetime(df.index).date
    df.index.name = "date"

    df = df.rename(columns={
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
    })

    # Compute EMAs on sorted close data
    df = df.sort_index()
    df["ema21"] = df["close"].ewm(span=21, adjust=False).mean()
    df["ema60"] = df["close"].ewm(span=60, adjust=False).mean()

    return df[["open", "high", "low", "close", "volume", "ema21", "ema60"]]


def save_to_parquet(symbol: str, df: pd.DataFrame) -> None:
    """Save full history to parquet file, merging with existing data."""
    parquet_path = DATA_DIR / f"{symbol}.parquet"

    if parquet_path.exists():
        existing = pd.read_parquet(parquet_path)
        combined = pd.concat([existing, df[~df.index.isin(existing.index)]])
        combined = combined.sort_index()
    else:
        combined = df

    combined.to_parquet(parquet_path)
    print(f"    parquet: {len(combined)} rows at {parquet_path}")


async def save_to_db(symbol: str, df: pd.DataFrame) -> int:
    """Upsert OHLC rows into Postgres. Returns count of new rows."""
    if df.empty:
        return 0

    async with async_session() as session:
        inserted = 0
        for idx, row in df.iterrows():
            stmt = pg_insert(OHLC).values(
                symbol=symbol,
                date=idx,
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=int(row["volume"]),
                ema21=row["ema21"] if not pd.isna(row["ema21"]) else None,
                ema60=row["ema60"] if not pd.isna(row["ema60"]) else None,
            ).on_conflict_do_update(
                constraint="ohlc_symbol_date_key",
                set_={
                    "open": row["open"],
                    "high": row["high"],
                    "low": row["low"],
                    "close": row["close"],
                    "volume": int(row["volume"]),
                    "ema21": row["ema21"] if not pd.isna(row["ema21"]) else None,
                    "ema60": row["ema60"] if not pd.isna(row["ema60"]) else None,
                },
            )
            await session.execute(stmt)
            inserted += 1

        await session.commit()
        return inserted


async def ingest_backfill() -> None:
    """Initial load: 2 years of daily OHLC for all active ETFs."""
    print("=== OHLC BACKFILL ===")
    symbols = await get_active_symbols()
    print(f"Active ETFs: {len(symbols)}")

    for symbol in symbols:
        print(f"\n{symbol}:")
        df = download_and_compute(symbol)
        if df.empty:
            continue

        save_to_parquet(symbol, df)
        n = await save_to_db(symbol, df)
        print(f"    db: {n} rows upserted")


async def ingest_update() -> None:
    """Daily update: fetch latest data for all active ETFs."""
    print("=== OHLC UPDATE ===")
    symbols = await get_active_symbols()
    print(f"Active ETFs: {len(symbols)}")

    today = date.today()
    for symbol in symbols:
        last_date = await get_last_date(symbol)
        start = last_date - timedelta(days=7) if last_date else today - timedelta(days=30)

        print(f"\n{symbol} (last in DB: {last_date}):")
        df = download_and_compute(symbol, start_date=start)
        if df.empty:
            continue

        df = df[df.index > (last_date or date(2000, 1, 1))]
        if df.empty:
            print("    already up to date")
            continue

        save_to_parquet(symbol, df)
        n = await save_to_db(symbol, df)
        print(f"    db: {n} new rows upserted")


async def main() -> None:
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "update"

    if mode == "backfill":
        await ingest_backfill()
    elif mode == "update":
        await ingest_update()
    else:
        print(f"Unknown mode: {mode}. Use 'backfill' or 'update'.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
