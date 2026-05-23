"""Admin endpoints (KATS controls)."""

from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from backend.app.db import async_session
from backend.app.models.etf import ETF
from backend.app.models.strategy_params import StrategyParam
from backend.app.schemas.admin import StrategyParamUpdate

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/strategy-params")
async def list_strategy_params() -> list[dict[str, object]]:
    async with async_session() as session:
        result = await session.execute(select(StrategyParam).order_by(StrategyParam.param_name))
        return [
            {"param_name": r.param_name, "param_value": r.param_value, "description": r.description}
            for r in result.scalars().all()
        ]


@router.put("/strategy-params/{param_name}")
async def update_strategy_param(param_name: str, body: StrategyParamUpdate) -> dict[str, str]:
    async with async_session() as session:
        result = await session.execute(
            select(StrategyParam).where(StrategyParam.param_name == param_name)
        )
        param = result.scalar_one_or_none()
        if param is None:
            raise HTTPException(status_code=404, detail=f"Unknown param: {param_name}")

        from datetime import datetime
        param.param_value = body.param_value  # type: ignore[assignment]
        param.updated_at = datetime.now()
        await session.commit()
    return {"status": "updated", "param_name": param_name}


@router.get("/etfs")
async def list_etfs_admin() -> list[dict[str, object]]:
    async with async_session() as session:
        result = await session.execute(select(ETF).order_by(ETF.symbol))
        return [
            {
                "symbol": e.symbol,
                "name": e.name,
                "category": e.category.value,
                "active": e.active,
            }
            for e in result.scalars().all()
        ]


@router.put("/etfs/{symbol}")
async def toggle_etf(symbol: str, active: bool = True) -> dict[str, object]:
    async with async_session() as session:
        result = await session.execute(select(ETF).where(ETF.symbol == symbol))
        etf = result.scalar_one_or_none()
        if etf is None:
            raise HTTPException(status_code=404, detail=f"Unknown ETF: {symbol}")
        etf.active = active
        await session.commit()
    return {"symbol": symbol, "active": active}


@router.post("/pause")
async def pause_system() -> dict[str, str]:
    async with async_session() as session:
        result = await session.execute(
            select(StrategyParam).where(StrategyParam.param_name == "system_status")
        )
        param = result.scalar_one_or_none()
        if param is None:
            param = StrategyParam(
                param_name="system_status", param_value="paused",
                description="System operational status",
            )
            session.add(param)
        else:
            param.param_value = "paused"  # type: ignore[assignment]
        await session.commit()
    return {"status": "paused"}


@router.post("/resume")
async def resume_system() -> dict[str, str]:
    async with async_session() as session:
        result = await session.execute(
            select(StrategyParam).where(StrategyParam.param_name == "system_status")
        )
        param = result.scalar_one_or_none()
        if param is None:
            param = StrategyParam(
                param_name="system_status", param_value="running",
                description="System operational status",
            )
            session.add(param)
        else:
            param.param_value = "running"  # type: ignore[assignment]
        await session.commit()
    return {"status": "running"}


@router.get("/audit-log")
async def audit_log(lines: int = 50) -> list[str]:
    from pathlib import Path
    log_path = Path("wiki/log.md")
    if not log_path.exists():
        return []
    content = log_path.read_text().split("\n")
    return [line for line in content if line.startswith("## [")][-lines:]


class RunBacktestRequest(BaseModel):
    start_date: str | None = None  # ISO date string, e.g. "2025-01-01"
    total_corpus: float | None = None  # Override default corpus


@router.post("/run-backtest")
async def run_backtest(body: RunBacktestRequest | None = None) -> dict[str, str]:
    """Trigger backtest for all ETFs and update wiki.

    Optional body: {start_date: "2025-01-01", total_corpus: 15000000}
    """
    from backend.app.backtest.runner import run_backtest_all
    from backend.app.routers.backtest import save_backtest_results

    start_date = None
    if body and body.start_date:
        try:
            start_date = date.fromisoformat(body.start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid date: {body.start_date}")

    try:
        results = await run_backtest_all(start_date=start_date)
        await save_backtest_results(
            results,
            start_date_str=body.start_date if body else None,
            total_corpus=body.total_corpus if body else None,
        )
        total_trades = sum(r.total_trades for r in results.values())
        total_pnl = sum(r.total_pnl for r in results.values())
        return {
            "status": "completed",
            "etfs_tested": str(len(results)),
            "total_trades": str(total_trades),
            "total_pnl": f"₹{total_pnl:,.0f}",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-eod-scan")
async def run_eod_scan() -> dict[str, str]:
    """Trigger end-of-day scan for all active ETFs."""
    from datetime import date

    from backend.app.broker.paper_broker import PaperBroker
    from backend.app.broker.state_loader import (
        get_active_symbols,
        load_ohlc_bars,
        load_strategy_params,
    )
    from backend.app.db import async_session
    from backend.app.strategy.models import PositionState
    from backend.app.strategy.scanner import scan_etf

    try:
        params = await load_strategy_params()
        symbols = await get_active_symbols()
        today = date.today()
        signals_fired = 0

        async with async_session() as session:
            for sym in symbols:
                bars = await load_ohlc_bars(sym, lookback_days=120)
                if len(bars) < 60:
                    continue
                position = PositionState()
                sigs = scan_etf(sym, bars, position, today, params)
                for sig in sigs:
                    try:
                        await PaperBroker.process_signal(sig, session)
                        signals_fired += 1
                    except ValueError:
                        pass
            if signals_fired > 0:
                await session.commit()

        return {
            "status": "completed",
            "etfs_scanned": str(len(symbols)),
            "signals_fired": str(signals_fired),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-morning-execute")
async def run_morning_execute() -> dict[str, str]:
    """Trigger morning fill verification for pending orders."""
    from datetime import datetime

    from sqlalchemy import select

    from backend.app.db import async_session
    from backend.app.models.trade import OrderStatus, Trade

    try:
        async with async_session() as session:
            result = await session.execute(
                select(Trade).where(Trade.order_status == OrderStatus.PENDING)
            )
            pending = result.scalars().all()
            filled = 0
            for t in pending:
                t.fill_price = t.limit_price
                t.order_status = OrderStatus.FILLED
                t.filled_at = datetime.now()
                filled += 1
            if filled > 0:
                await session.commit()

        return {"status": "completed", "orders_filled": str(filled)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
