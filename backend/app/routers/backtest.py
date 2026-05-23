"""Backtest API endpoints — read cached results."""

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/api/backtest", tags=["backtest"])

CACHE_DIR = Path("data/backtest")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _load_cache() -> dict[str, Any]:
    cache_file = CACHE_DIR / "results.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text())  # type: ignore[no-any-return]
    return {}


def _save_cache(data: dict[str, Any]) -> None:
    cache_file = CACHE_DIR / "results.json"
    cache_file.write_text(json.dumps(data, indent=2, default=str))


@router.get("/summary")
async def backtest_summary() -> dict[str, Any]:
    """Return aggregate backtest results across all ETFs."""
    cache = _load_cache()
    if not cache:
        return {"status": "no data", "message": "Run backtest first"}

    # Top-level metadata (stored by save_backtest_results)
    meta = cache.pop("_meta", {})

    results = list(cache.values())
    total_pnl = sum(r["total_pnl"] for r in results)
    total_trades = sum(r["total_trades"] for r in results)
    winning = sum(r["winning_trades"] for r in results)
    losing = sum(r["losing_trades"] for r in results)

    # Collect currently held positions: if the LAST trade for an ETF is entry/addon,
    # the position is still open. Walk trades to compute capital deployed per holding.
    currently_holding: list[dict[str, Any]] = []
    total_invested = 0.0
    for r in results:
        trades = r.get("trades", [])
        if not trades:
            continue
        last_trade = trades[-1]
        if last_trade.get("action") in ("entry", "addon"):
            # Walk forward to find the entry for this open position
            # and sum capital deployed (entry + subsequent addons)
            entry_trade = None
            last_addon = None
            capital_deployed = 0.0
            # Walk backward from end to find the entry that started this holding
            for t in reversed(trades):
                if t.get("action") == "entry":
                    entry_trade = t
                    break
                if t.get("action") == "addon" and last_addon is None:
                    last_addon = t
            if entry_trade:
                # Sum capital from this entry and all subsequent addons
                addon_units = 0.0
                for t in trades:
                    if t is entry_trade:
                        capital_deployed = t.get("tranche_amount", 0)
                        addon_units = t.get("units", 0)
                    elif t.get("action") == "addon" and capital_deployed > 0:
                        capital_deployed += t.get("tranche_amount", 0)
                        addon_units += t.get("units", 0)
                    elif t.get("action") in ("exit_profit", "exit_time", "exit_sl"):
                        capital_deployed = 0
                        addon_units = 0
                holding: dict[str, Any] = {
                    "symbol": r["symbol"],
                    "entry_date": entry_trade["entry_date"],
                    "entry_price": entry_trade["entry_price"],
                    "capital_deployed": capital_deployed,
                }
                if last_addon:
                    holding["last_addon_date"] = last_addon["entry_date"]
                    holding["last_addon_price"] = last_addon["entry_price"]
                currently_holding.append(holding)
                total_invested += capital_deployed

    total_corpus = meta.get("total_corpus", 15_000_000)
    available_capital = total_corpus - total_invested

    return {
        "etfs_tested": len(results),
        "total_trades": total_trades,
        "winning_trades": winning,
        "losing_trades": losing,
        "win_rate": round(winning / total_trades * 100, 1) if total_trades > 0 else 0,
        "total_pnl": round(total_pnl, 2),
        "total_corpus": total_corpus,
        "total_invested": round(total_invested, 2),
        "available_capital": round(available_capital, 2),
        "start_date": meta.get("start_date"),
        "currently_holding": currently_holding,
        "etfs": sorted(results, key=lambda r: r.get("total_return_pct", 0), reverse=True),
    }


@router.get("/portfolio-history")
async def portfolio_history() -> list[dict[str, object]]:
    """Return month-by-month portfolio state: ETFs held, capital deployed, available.

    Replays all trades chronologically and samples state at each month boundary.
    """
    from datetime import date, timedelta

    cache = _load_cache()
    meta = cache.pop("_meta", {})
    total_corpus = meta.get("total_corpus", 15_000_000)

    # Collect all trades with dates, sorted chronologically
    events: list[tuple[str, str, float]] = []  # (date, action, amount)
    for symbol, r in cache.items():
        for t in r.get("trades", []):
            ed = t.get("entry_date", "")
            if not ed:
                continue
            action = t.get("action", "")
            amount = t.get("tranche_amount", 0) or 0
            events.append((ed, action, amount))

    if not events:
        return []

    events.sort(key=lambda x: x[0])
    first_date = date.fromisoformat(events[0][0])
    last_date = date.today()

    # Generate all months in range for sampling
    monthly: dict[str, dict[str, float]] = {}

    # Group trades by symbol to process each ETF's sequence
    trades_by_symbol: dict[str, list[dict[str, Any]]] = {}
    for symbol, r in cache.items():
        trades_by_symbol[symbol] = r.get("trades", [])

    # Generate all months in range
    d = date(first_date.year, first_date.month, 1)
    while d <= last_date:
        monthly[d.strftime("%Y-%m")] = {"etfs_held": 0, "capital_deployed": 0}
        # Move to next month
        if d.month == 12:
            d = date(d.year + 1, 1, 1)
        else:
            d = date(d.year, d.month + 1, 1)

    # For each month, replay trades to compute state at end of that month
    for month_key in sorted(monthly.keys()):
        month_end = (
            date(int(month_key[:4]), int(month_key[5:7]), 28) + timedelta(days=4)
        ).replace(day=1) - timedelta(days=1)

        active: set[str] = set()
        deployed: dict[str, float] = {}

        for symbol, trades in trades_by_symbol.items():
            capital = 0.0
            for t in trades:
                t_date = date.fromisoformat(t["entry_date"])
                if t_date > month_end:
                    break
                action = t.get("action", "")
                amount = t.get("tranche_amount", 0) or 0
                if action == "entry":
                    capital = amount
                elif action == "addon" and capital > 0:
                    capital += amount
                elif action in ("exit_profit", "exit_time", "exit_sl"):
                    capital = 0
            if capital > 0:
                active.add(symbol)
                deployed[symbol] = capital

        monthly[month_key] = {
            "etfs_held": len(active),
            "capital_deployed": sum(deployed.values()),
        }

    result: list[dict[str, object]] = []
    for month_key in sorted(monthly.keys()):
        m = monthly[month_key]
        deployed = m["capital_deployed"]
        result.append({
            "month": month_key + "-01",
            "month_label": month_key,
            "etfs_held": m["etfs_held"],
            "capital_deployed": round(deployed, 2),
            "capital_available": round(total_corpus - deployed, 2),
        })

    return result


@router.get("/{symbol}")
async def backtest_symbol(symbol: str) -> dict[str, Any]:
    """Return backtest results for a single ETF."""
    cache = _load_cache()
    if symbol not in cache:
        return {"status": "not found", "symbol": symbol}
    return cache[symbol]  # type: ignore[no-any-return]


async def save_backtest_results(
    results: dict[str, Any],
    start_date_str: str | None = None,
    total_corpus: float | None = None,
) -> None:
    """Save backtest results to cache and populate wiki."""
    from backend.app.backtest.runner import BacktestResult

    # Save to JSON cache
    cache_data: dict[str, dict[str, Any]] = {}
    cache_data["_meta"] = {
        "start_date": start_date_str,
        "total_corpus": total_corpus or 15_000_000,
    }
    for symbol, r in results.items():
        if not isinstance(r, BacktestResult):
            continue
        cache_data[symbol] = {
            "symbol": r.symbol,
            "total_trades": r.total_trades,
            "winning_trades": r.winning_trades,
            "losing_trades": r.losing_trades,
            "win_rate": r.win_rate,
            "total_pnl": r.total_pnl,
            "total_return_pct": r.total_return_pct,
            "max_drawdown_pct": r.max_drawdown_pct,
            "avg_hold_days": r.avg_hold_days,
            "trades": [
                {
                    "action": t.action,
                    "entry_date": str(t.entry_date),
                    "exit_date": str(t.exit_date) if t.exit_date else None,
                    "entry_price": t.entry_price,
                    "exit_price": t.exit_price,
                    "tranche_amount": t.tranche_amount,
                    "units": t.units,
                    "pnl": t.pnl,
                    "pnl_pct": t.pnl_pct,
                    "hold_days": t.hold_days,
                }
                for t in r.trades
            ],
        }
    _save_cache(cache_data)

    # Write wiki summary
    from datetime import date

    from backend.app.wiki.writer import _write_atomic

    total_pnl = sum(r.total_pnl for r in results.values() if isinstance(r, BacktestResult))
    total_trades = sum(r.total_trades for r in results.values() if isinstance(r, BacktestResult))
    winning = sum(r.winning_trades for r in results.values() if isinstance(r, BacktestResult))
    wr = winning / total_trades * 100 if total_trades > 0 else 0

    lines = [
        f"# Backtest Results — {date.today().isoformat()}",
        "",
        "## Aggregate",
        f"- **ETFs tested:** {len(results)}",
        f"- **Total trades:** {total_trades}",
        f"- **Win rate:** {wr:.1f}%",
        f"- **Total P&L:** ₹{total_pnl:,.0f}",
        f"- **Period:** {date.today().year - 2} to {date.today().isoformat()}",
        "",
        "## Per-ETF Performance",
        "| Symbol | Trades | Win Rate | P&L | Return % | Max DD % | Avg Hold (d) |",
        "|--------|--------|----------|-----|----------|----------|--------------|",
    ]

    for symbol, r in sorted(results.items()):
        if not isinstance(r, BacktestResult):
            continue
        lines.append(
            f"| {r.symbol:12s} | {r.total_trades:6d} | "
            f"{r.win_rate:5.0f}% | ₹{r.total_pnl:,.0f} | "
            f"{r.total_return_pct:5.1f}% | {r.max_drawdown_pct:5.1f}% | "
            f"{r.avg_hold_days:4.0f} |"
        )

    _write_atomic(str(Path("wiki/backtest/summary.md")), "\n".join(lines) + "\n")

    # Write per-ETF trade history into each ETF wiki page
    from backend.app.wiki.writer import append_backtest_section
    for symbol, r in results.items():
        if not isinstance(r, BacktestResult) or not r.trades:
            continue
        trades_data: list[dict[str, object]] = [
            {
                "action": t.action,
                "entry_date": str(t.entry_date),
                "exit_date": str(t.exit_date) if t.exit_date else None,
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "pnl": t.pnl,
                "pnl_pct": t.pnl_pct,
                "hold_days": t.hold_days,
            }
            for t in r.trades
        ]
        append_backtest_section(symbol, trades_data)

    # Append to log.md
    from backend.app.jobs.wiki_logger import _append_atomic
    log_entry = (
        f"## [{date.today().isoformat()}] BACKTEST | ALL | "
        f"{len(results)} ETFs, {total_trades} trades, win rate {wr:.0f}%, "
        f"total P&L ₹{total_pnl:,.0f}\n"
    )
    _append_atomic("wiki/log.md", log_entry)
