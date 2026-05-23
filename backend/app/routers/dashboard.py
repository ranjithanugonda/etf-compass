"""Dashboard endpoints — public (no auth)."""

from datetime import date, timedelta

from fastapi import APIRouter
from sqlalchemy import func, select

from backend.app.db import async_session
from backend.app.models.position import Position, PositionStatus
from backend.app.models.trade import Trade, TradeAction
from backend.app.schemas.dashboard import (
    DecisionDashboard,
    DiagnosticDashboard,
    EvidenceDashboard,
    MonthlyActivity,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/decision", response_model=DecisionDashboard)
async def decision() -> DecisionDashboard:
    async with async_session() as session:
        # Total corpus from strategy_params
        from backend.app.models.strategy_params import StrategyParam
        result = await session.execute(
            select(StrategyParam).where(StrategyParam.param_name == "total_corpus")
        )
        corpus_row = result.scalar_one_or_none()
        total_corpus = float(corpus_row.param_value) if corpus_row else 15_000_000  # type: ignore[arg-type]

        # Capital utilized from active positions
        r2 = await session.execute(
            select(func.coalesce(func.sum(Position.total_capital_deployed), 0.0)).where(
                Position.status == PositionStatus.ACTIVE
            )
        )
        capital_utilized = r2.scalar_one()

        # Avg holding duration for closed positions
        r3 = await session.execute(
            select(func.avg(
                Position.exited_at - Position.entered_at
            )).where(
                Position.status == PositionStatus.FLAT,
                Position.entered_at.isnot(None),
                Position.exited_at.isnot(None),
            )
        )
        avg_days = r3.scalar_one()

        # YTD ROI: realized P&L this year
        year_start = date(date.today().year, 1, 1)
        r4 = await session.execute(
            select(func.coalesce(func.sum(
                (Trade.fill_price - Trade.limit_price) * Trade.quantity
            ), 0.0)).where(
                Trade.action.in_([
                    TradeAction.EXIT_PROFIT, TradeAction.EXIT_TIME, TradeAction.EXIT_SL
                ]),
                Trade.filled_at >= year_start,
                Trade.fill_price.isnot(None),
            )
        )
        realized_pnl = r4.scalar_one()

        # Entry trades: total buy cost
        r5 = await session.execute(
            select(func.coalesce(func.sum(
                Trade.fill_price * Trade.quantity
            ), 0.0)).where(
                Trade.action.in_([TradeAction.ENTRY, TradeAction.ADDON]),
                Trade.filled_at >= year_start,
                Trade.fill_price.isnot(None),
            )
        )
        buy_cost = r5.scalar_one()

        ytd_roi = (realized_pnl / buy_cost * 100) if buy_cost > 0 else 0.0  # type: ignore[operator]
        avg_months = (avg_days / 30.44) if avg_days else 0.0
        cap_pct = (capital_utilized / total_corpus * 100) if total_corpus > 0 else 0.0

    return DecisionDashboard(
        ytd_roi_pct=round(ytd_roi, 2),
        expected_roi_pct=13.0,  # from PRD base case
        avg_duration_months=round(avg_months, 1),
        expected_holding_months=4.0,
        capital_utilized_pct=round(cap_pct, 1),
        total_corpus=total_corpus,
    )


@router.get("/diagnostic", response_model=DiagnosticDashboard)
async def diagnostic() -> DiagnosticDashboard:
    async with async_session() as session:
        months: list[MonthlyActivity] = []
        today = date.today()

        for i in range(11, -1, -1):
            month_start = date(today.year, today.month, 1) - timedelta(days=1)
            for _ in range(i):
                month_start = (month_start.replace(day=1) - timedelta(days=1)).replace(day=1)
            if i == 0:
                month_start = today.replace(day=1)
            else:
                month_start = (today.replace(day=1) - timedelta(days=i * 31)).replace(day=1)
            month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)

            # Count trades in this month
            counts = {"entries": 0, "addons": 0, "profit_exits": 0, "time_exits": 0}
            for action, key in [
                (TradeAction.ENTRY, "entries"),
                (TradeAction.ADDON, "addons"),
                (TradeAction.EXIT_PROFIT, "profit_exits"),
                (TradeAction.EXIT_TIME, "time_exits"),
            ]:
                result = await session.execute(
                    select(func.count(Trade.id)).where(
                        Trade.action == action,
                        Trade.filled_at >= month_start,
                        Trade.filled_at < month_end,
                    )
                )
                counts[key] = result.scalar_one()

            months.append(MonthlyActivity(
                month=month_start.strftime("%Y-%m"),
                new_positions=counts["entries"],
                addons=counts["addons"],
                profit_exits=counts["profit_exits"],
                time_exits=counts["time_exits"],
            ))

    return DiagnosticDashboard(rolling_12_months=months)


@router.get("/diagnostic/data")
async def diagnostic_data(
    symbol: str = "ALL",
    source: str = "backtest",
) -> list[dict[str, object]]:
    """Monthly ROI + activity counts, filterable by ETF and source.

    Query params:
      symbol: ETF symbol or "ALL" for aggregate across all ETFs
      source: "backtest" (from 2-year simulation) or "live" (from DB trades)
    """
    import json
    from collections import defaultdict
    from datetime import date, timedelta
    from pathlib import Path

    from backend.app.models.strategy_params import StrategyParam

    monthly_pnl: dict[str, float] = defaultdict(float)
    monthly_counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {"entries": 0, "addons": 0, "profit_exits": 0, "time_exits": 0}
    )
    total_corpus = 15_000_000

    async with async_session() as session:
        r = await session.execute(
            select(StrategyParam).where(StrategyParam.param_name == "total_corpus")
        )
        row = r.scalar_one_or_none()
        if row:
            total_corpus = float(row.param_value)  # type: ignore[arg-type]

    if source == "backtest":
        cache_file = Path("data/backtest/results.json")
        if cache_file.exists():
            cache = json.loads(cache_file.read_text())
            targets = (
                [cache[symbol]] if symbol != "ALL" and symbol in cache
                else list(cache.values())
            )
            for data in targets:
                for t in data.get("trades", []):
                    action = t.get("action", "")
                    ed = t.get("entry_date") or ""
                    xd = t.get("exit_date")
                    if xd and t.get("pnl") is not None:
                        monthly_pnl[xd[:7]] += t["pnl"]
                        k = "profit_exits" if action == "exit_profit" else "time_exits"
                        monthly_counts[xd[:7]][k] += 1
                    if action in ("entry", "addon") and ed:
                        k = "entries" if action == "entry" else "addons"
                        monthly_counts[ed[:7]][k] += 1

    else:  # live
        from backend.app.models.position import Position
        async with async_session() as session:
            subq = select(Position.id)
            if symbol != "ALL":
                subq = subq.where(Position.etf_symbol == symbol)
            subq = subq.scalar_subquery()

            result_q = await session.execute(
                select(Trade).where(Trade.position_id.in_(subq)).order_by(Trade.filled_at)
            )
            for t in result_q.scalars().all():
                if not t.filled_at:
                    continue
                m = t.filled_at.strftime("%Y-%m")
                if t.fill_price and t.limit_price:
                    qty = t.quantity
                    pnl = (t.fill_price - t.limit_price) * qty
                    exit_actions = (
                        TradeAction.EXIT_PROFIT, TradeAction.EXIT_TIME, TradeAction.EXIT_SL
                    )
                    if t.action in exit_actions:
                        monthly_pnl[m] += pnl
                        if t.action == TradeAction.EXIT_PROFIT:
                            k = "profit_exits"
                        else:
                            k = "time_exits"  # SL exits grouped with time exits
                        monthly_counts[m][k] += 1
                if t.action == TradeAction.ENTRY:
                    monthly_counts[m]["entries"] += 1
                elif t.action == TradeAction.ADDON:
                    monthly_counts[m]["addons"] += 1

    today = date.today()
    result: list[dict[str, object]] = []
    for i in range(11, -1, -1):
        d = today.replace(day=1) - timedelta(days=i * 31)
        d = d.replace(day=1)
        key = d.strftime("%Y-%m")
        pnl = monthly_pnl.get(key, 0)
        counts = monthly_counts.get(
            key, {"entries": 0, "addons": 0, "profit_exits": 0, "time_exits": 0}
        )
        roi = round(pnl / total_corpus * 100, 2)
        result.append({
            "month": d.strftime("%Y-%m-%d"),
            "month_label": key,
            "pnl": round(pnl, 2),
            "roi_pct": roi,
            "new_positions": counts["entries"],
            "addons": counts["addons"],
            "profit_exits": counts["profit_exits"],
            "time_exits": counts["time_exits"],
        })

    return result


@router.get("/evidence", response_model=EvidenceDashboard)
async def evidence() -> EvidenceDashboard:
    async with async_session() as session:
        # Active positions
        pos_result = await session.execute(
            select(Position).where(Position.status == PositionStatus.ACTIVE)
        )
        positions: list[dict[str, object]] = []
        for p in pos_result.scalars().all():
            positions.append({
                "symbol": p.etf_symbol,
                "status": p.status.value,
                "tranches_used": p.tranches_used,
                "capital_deployed": p.total_capital_deployed,
                "wac": p.weighted_avg_cost,
                "entered_at": str(p.entered_at) if p.entered_at else None,
            })

        # Recent trades
        trade_result = await session.execute(
            select(Trade).order_by(Trade.filled_at.desc().nullslast()).limit(20)
        )
        recent: list[dict[str, object]] = []
        for t in trade_result.scalars().all():
            recent.append({
                "id": t.id,
                "action": t.action.value,
                "tranche_number": t.tranche_number,
                "quantity": t.quantity,
                "fill_price": t.fill_price,
                "filled_at": str(t.filled_at) if t.filled_at else None,
            })

        # Wiki pages
        from pathlib import Path
        wiki_base = Path("wiki")
        etfs_dir = wiki_base / "etfs"
        wiki_pages: list[str] = []
        if etfs_dir.exists():
            wiki_pages = sorted(f.stem for f in etfs_dir.glob("*.md"))

    return EvidenceDashboard(
        positions=positions,
        recent_trades=recent,
        wiki_pages=wiki_pages,
    )
