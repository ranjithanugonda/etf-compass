"""Append structured entries to wiki/log.md. Atomic writes."""

import os
from datetime import date
from pathlib import Path

from backend.app.strategy.models import Signal, SignalAction

WIKI_DIR = Path("wiki")
LOG_PATH = WIKI_DIR / "log.md"


def log_signal(today: date, signal: Signal) -> None:
    """Append a SIGNAL entry to the wiki log."""
    entry = _format_signal(today, signal)
    _append_atomic(str(LOG_PATH), entry)


def log_fill(today: date, symbol: str, units: int, price: float) -> None:
    """Append a FILL entry to the wiki log."""
    entry = (
        f"## [{today.isoformat()}] FILL | {symbol} | "
        f"filled {units} units @ {price:.2f}\n"
    )
    _append_atomic(str(LOG_PATH), entry)


def _format_signal(today: date, signal: Signal) -> str:
    action_map = {
        SignalAction.ENTRY: "ENTRY",
        SignalAction.ADDON: "ADDON",
        SignalAction.EXIT_PROFIT: "EXIT-PROFIT",
        SignalAction.EXIT_TIME: "EXIT-TIME",
        SignalAction.EXIT_SL: "EXIT-SL",
    }
    action_label = action_map.get(signal.action, signal.action.value.upper())
    return (
        f"## [{today.isoformat()}] SIGNAL | {signal.symbol} | "
        f"{action_label} tranche ₹{signal.tranche_amount:,.0f} — {signal.reason}\n"
    )


def _append_atomic(path: str, text: str) -> None:
    """Append to file atomically: write temp + fsync + rename."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    if os.path.exists(path):
        with open(path) as f:
            existing = f.read()
    else:
        existing = ""

    new_content = existing + text

    tmp_path = path + ".tmp"
    with open(tmp_path, "w") as f:
        f.write(new_content)
        f.flush()
        os.fsync(f.fileno())

    os.replace(tmp_path, path)
