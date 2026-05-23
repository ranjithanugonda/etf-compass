"""Wiki page writer — generates markdown pages from templates and DB data.

Uses Claude for narrative sections when ANTHROPIC_API_KEY is available.
All writes are atomic (temp file → fsync → rename).
"""

import os
from datetime import date
from pathlib import Path

from backend.app.strategy.models import OHLCBar, PositionState, Signal

WIKI_DIR = Path("wiki")
SCHEMA_PATH = Path("WIKI_SCHEMA.md")


def _write_atomic(path: str, content: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, path)


def _maybe_claude_narrative(prompt: str) -> str:
    """Call Claude for a short narrative. Returns empty string if no API key."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key or api_key == "sk-ant-...":
        return ""

    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system="You write concise trading journal narratives for an ETF accumulation system. "
                   "Write 2-3 sentences in plain English. Be specific about what the data shows. "
                   "No markdown headers, no bullet points, just flowing prose.",
            messages=[{"role": "user", "content": prompt}],
        )
        block = message.content[0]
        return block.text if hasattr(block, "text") else ""
    except Exception:
        return ""


def _format_bar_summary(bars: list[OHLCBar]) -> str:
    if not bars:
        return "_No OHLC data available_"
    latest = bars[-1]
    high_60 = max(b.close for b in bars[-60:]) if len(bars) >= 2 else latest.close
    return (
        f"Latest close: ₹{latest.close:.2f} | "
        f"EMA21: {latest.ema21:.2f}" if latest.ema21 else "EMA21: n/a"
    ) + (
        f" | EMA60: {latest.ema60:.2f}" if latest.ema60 else " | EMA60: n/a"
    ) + (
        f" | 60-day high: ₹{high_60:.2f}"
    )


def write_etf_page(
    symbol: str,
    name: str,
    category: str,
    amc: str,
    underlying: str,
    beta: float | None,
    atr: float | None,
    position: PositionState | None,
    bars: list[OHLCBar],
    recent_signals: list[Signal],
    decisions: list[str],
) -> str:
    """Write or update wiki/etfs/{SYMBOL}.md. Returns the path."""
    is_active = position is not None and position.is_active
    pos_status = "Active" if is_active else "Flat"

    # Build structured sections
    state_lines = [
        f"- **Position status:** {pos_status}",
    ]
    if position and is_active:
        state_lines.extend([
            f"- **Tranches used:** {position.tranches_used} / 9",
            f"- **Capital deployed:** ₹{position.total_capital_deployed:,.0f}",
            f"- **LBP:** ₹{position.last_buy_price:.2f}" if position.last_buy_price else "",
            f"- **WAC:** ₹{position.weighted_avg_cost:.2f}" if position.weighted_avg_cost else "",
            f"- **Total units:** {position.total_units:.0f}",
            f"- **Entered:** {position.entered_at.isoformat()}" if position.entered_at else "",
        ])
    state_text = "\n".join(line for line in state_lines if line)

    # Narrative: ask Claude why we are/aren't in this ETF
    bar_summary = _format_bar_summary(bars)
    narrative_prompt = (
        f"ETF: {symbol} ({name}) — {category}, {amc}\n"
        f"Position: {pos_status}. {state_text}\n"
        f"Price data: {bar_summary}\n"
        f"Recent signals: {len(recent_signals)}\n\n"
        f"Write 2-3 sentences explaining why the system "
        f"{'holds' if is_active else 'does not hold'} "  # noqa: E501
        f"this ETF right now. Reference the trend, price action, and any recent signals."
    )
    narrative = _maybe_claude_narrative(narrative_prompt) or (
        f"{symbol} is currently "
        f"{'in an active position' if is_active else 'flat — no position held'}."  # noqa: E501
        f"{' The system is accumulating via tranche-based entries.' if is_active else ''}"
    )

    # Decision history
    decision_lines = "\n".join(
        f"- [[{d}]]" for d in decisions
    ) if decisions else "- _No decisions yet_"

    # Signals summary
    signal_lines = "\n".join(
        f"- {s.action.value}: ₹{s.tranche_amount:,.0f} @ ₹{s.limit_price:.2f} — {s.reason}"
        for s in recent_signals[-5:]
    ) if recent_signals else "- _No recent signals_"

    content = f"""# {symbol} — {name} ({amc})

- **Category:** {category}
- **Beta / ATR:** {beta} / {atr}
- **Underlying exposure:** {underlying}

## Current state (as of {date.today().isoformat()})
{state_text}

## Why we are (or are not) in this ETF
{narrative}

## Recent signals
{signal_lines}

## Decision history
{decision_lines}
"""
    path = WIKI_DIR / "etfs" / f"{symbol}.md"
    _write_atomic(str(path), content)
    return str(path)


def write_decision_page(
    symbol: str,
    signal: Signal,
    bars: list[OHLCBar],
    position: PositionState | None,
) -> str:
    """Write wiki/decisions/{date}-{SYMBOL}-{action}.md. Returns the path."""
    today = date.today().isoformat()
    action = signal.action.value
    latest = bars[-1] if bars else None

    price_section = ""
    if latest:
        price_section = (
            f"- **Trend:** (close ₹{latest.close:.2f}, "
            f"EMA21 {latest.ema21 or 'n/a'}, EMA60 {latest.ema60 or 'n/a'})\n"
        )

    pos_section = ""
    if position:
        pos_section = (
            f"- **LBP / WAC before action:** "
            f"₹{position.last_buy_price or 'n/a'} / ₹{position.weighted_avg_cost or 'n/a'}\n"
            f"- **Capital state:** {position.tranches_used}/9 tranches, "
            f"₹{position.total_capital_deployed:,.0f} deployed\n"
        )

    narrative_prompt = (
        f"ETF: {symbol}. Action: {action}. Amount: ₹{signal.tranche_amount:,.0f}.\n"
        f"Price: ₹{signal.limit_price:.2f}. Reason: {signal.reason}\n"
        f"Write one sentence explaining this trade decision in plain English."
    )
    narrative = _maybe_claude_narrative(narrative_prompt) or signal.reason

    content = f"""# {symbol} {action.upper()} — {today}

- **Action:** {action.upper()}
- **Trigger:** {signal.reason}

## Inputs
{price_section}{pos_section}
## Rule cited
{signal.reason}

## Outcome
- **Limit price:** ₹{signal.limit_price:.2f}
- **Tranche size:** ₹{signal.tranche_amount:,.0f}

## Narrative
{narrative}

## Related
- [[etfs/{symbol}]]
"""
    filename = f"{today}-{symbol}-{action}.md"
    path = WIKI_DIR / "decisions" / filename
    _write_atomic(str(path), content)
    return str(path)


def write_daily_summary(
    scan_date: date,
    signals: list[Signal],
    summary: dict[str, int],
) -> str:
    """Write wiki/daily/{YYYY-MM-DD}.md. Returns the path."""
    today = scan_date.isoformat()

    signal_list = "\n".join(
        f"- {s.symbol}: **{s.action.value.upper()}** — {s.reason}"
        for s in signals
    ) if signals else "- No signals generated today"

    narrative_prompt = (
        f"Daily scan for {today}. "
        f"Scanned: {summary.get('scanned', 0)} ETFs. "
        f"Entries: {summary.get('entries', 0)}, Add-ons: {summary.get('addons', 0)}, "
        f"Profit exits: {summary.get('profit_exits', 0)}, "
        f"Time exits: {summary.get('time_exits', 0)}. "  # noqa: E501
        f"Write 2 sentences tying today's activity to market context."
    )
    notes = _maybe_claude_narrative(narrative_prompt) or (
        f"Scanned {summary.get('scanned', 0)} ETFs. "
        f"{summary.get('entries', 0)} new entries, {summary.get('addons', 0)} add-ons, "
        f"{summary.get('profit_exits', 0)} profit exits, {summary.get('time_exits', 0)} time exits."
    )

    content = f"""# Daily scan — {today}

## Headline numbers
- New positions: {summary.get('entries', 0)}
- Add-ons: {summary.get('addons', 0)}
- Profit exits: {summary.get('profit_exits', 0)}
- Time exits: {summary.get('time_exits', 0)}
- ETFs scanned: {summary.get('scanned', 0)}

## Signals
{signal_list}

## Notes
{notes}
"""
    path = WIKI_DIR / "daily" / f"{today}.md"
    _write_atomic(str(path), content)
    return str(path)


def append_backtest_section(symbol: str, trades: list[dict[str, object]]) -> None:
    """Append or update the backtest trade history section on an ETF wiki page."""
    etf_page = WIKI_DIR / "etfs" / f"{symbol}.md"

    if etf_page.exists():
        existing = etf_page.read_text()
        # Remove any existing backtest section
        if "## Backtest Trade History" in existing:
            existing = existing.split("## Backtest Trade History")[0].rstrip()
    else:
        existing = f"# {symbol}\n"

    if not trades:
        return

    lines = [
        "",
        "## Backtest Trade History",
        "",
        (
            "| # | Action | Entry Date | Exit Date | "
            "Entry Price | Exit Price | Hold Days | P&L | Return % |"
        ),
        "|---|--------|------------|-----------|-------------|------------|-----------|-----|----------|",
    ]

    for i, t in enumerate(trades, 1):
        action = str(t.get("action", "")).replace("_", " ")
        entry_date = str(t.get("entry_date", ""))
        exit_date = str(t.get("exit_date", "")) if t.get("exit_date") else "—"
        entry_price = f"₹{float(t.get('entry_price', 0)):.2f}"
        exit_price = f"₹{float(t.get('exit_price', 0)):.2f}" if t.get("exit_price") else "—"
        hold_days = str(t.get("hold_days", "")) if t.get("hold_days") is not None else "—"
        pnl_val = t.get("pnl")
        pnl_str = f"₹{float(pnl_val):,.0f}" if pnl_val is not None else "—"
        pnl_pct_val = t.get("pnl_pct")
        pnl_pct_str = f"{float(pnl_pct_val):.1f}%" if pnl_pct_val is not None else "—"

        lines.append(
            f"| {i} | {action} | {entry_date} | {exit_date} | "
            f"{entry_price} | {exit_price} | {hold_days} | {pnl_str} | {pnl_pct_str} |"
        )

    lines.append("")
    _write_atomic(str(etf_page), existing + "\n".join(lines))
