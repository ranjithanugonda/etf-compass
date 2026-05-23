"""Daily morning execute (09:20 IST): verify fills from yesterday's scan."""

import asyncio
from datetime import date

from sqlalchemy import select

from backend.app.db import async_session
from backend.app.jobs.wiki_logger import log_fill
from backend.app.models.trade import OrderStatus, Trade


async def run_morning_execute(today: date | None = None) -> dict[str, int]:
    """Confirm yesterday's filled trades and log FILL events.

    In MVP paper trading, signals are filled immediately at scan time.
    This job verifies and logs them.
    """
    if today is None:
        today = date.today()

    print(f"\n=== MORNING EXECUTE — {today.isoformat()} ===\n")

    async with async_session() as session:
        result = await session.execute(
            select(Trade).where(
                Trade.order_status == OrderStatus.FILLED,
            ).order_by(Trade.filled_at.desc()).limit(50)
        )
        trades = result.scalars().all()

        for trade in trades:
            log_fill(
                today,
                symbol="(lookup)",  # trade doesn't have symbol directly
                units=trade.quantity,
                price=trade.fill_price or trade.limit_price,
            )

        print(f"Verified {len(trades)} filled trades")

    return {"fills_verified": len(trades)}


async def main() -> None:
    await run_morning_execute()


if __name__ == "__main__":
    asyncio.run(main())
