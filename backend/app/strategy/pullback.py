"""Pullback detector for entry signal qualification."""

from backend.app.strategy.models import OHLCBar


def detect_pullback(
    bars: list[OHLCBar],
    weekly_pct: float = 2.5,
    weekly_days: int = 5,
    monthly_pct: float = 5.0,
    monthly_days: int = 21,
) -> bool:
    """Check if the latest close qualifies as a pullback.

    PRD §5.1: pullback is valid when price declined from the highest close in
    the lookback period by at least weekly_pct% (over weekly_days) OR
    monthly_pct% (over monthly_days).

    Bars must be sorted by date ascending; the last bar is the current bar.
    """
    if len(bars) < 2:
        return False

    current_close = bars[-1].close

    weekly_window = bars[-weekly_days - 1:]
    weekly_high = max(b.close for b in weekly_window)
    if weekly_high > 0:
        weekly_decline = (weekly_high - current_close) / weekly_high * 100
        if weekly_decline >= weekly_pct:
            return True

    monthly_window = bars[-monthly_days - 1:]
    monthly_high = max(b.close for b in monthly_window)
    if monthly_high > 0:
        monthly_decline = (monthly_high - current_close) / monthly_high * 100
        if monthly_decline >= monthly_pct:
            return True

    return False
