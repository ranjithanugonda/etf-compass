from datetime import date

from backend.app.strategy.models import OHLCBar
from backend.app.strategy.pullback import detect_pullback


def make_bar(close: float, days_ago: int = 0) -> OHLCBar:
    from datetime import timedelta
    d = date.today() - timedelta(days=days_ago)
    return OHLCBar(date=d, open=close, high=close, low=close, close=close, volume=1000)


def make_bars(closes: list[float]) -> list[OHLCBar]:
    return [make_bar(c, len(closes) - 1 - i) for i, c in enumerate(closes)]


def test_empty_bars() -> None:
    assert detect_pullback([]) is False


def test_single_bar() -> None:
    assert detect_pullback([make_bar(100)]) is False


def test_weekly_pullback_triggered() -> None:
    # 5 days: high=105, current=102, decline = (105-102)/105 = 2.86% >= 2.5%
    closes = [100.0] * 20 + [105.0, 104.0, 103.0, 103.0, 102.0]
    bars = make_bars(closes)
    assert detect_pullback(bars, weekly_pct=2.5, weekly_days=5) is True


def test_weekly_pullback_not_triggered() -> None:
    # decline less than threshold
    closes = [100.0] * 20 + [105.0, 105.0, 105.0, 105.0, 104.9]
    bars = make_bars(closes)
    assert detect_pullback(bars, weekly_pct=2.5, weekly_days=5) is False


def test_monthly_pullback_triggered() -> None:
    # 21 days: high=110, current=104, decline = (110-104)/110 = 5.45% >= 5%
    closes = [100.0] * 10 + [110.0] + [106.0] * 10 + [104.0]
    bars = make_bars(closes)
    assert detect_pullback(bars, monthly_pct=5.0, monthly_days=21) is True


def test_weekly_trumps_monthly() -> None:
    # weekly trigger even if monthly doesn't
    closes = [95.0] * 20 + [105.0, 104.0, 102.0, 102.0, 102.0]
    bars = make_bars(closes)
    assert detect_pullback(bars, weekly_pct=2.5, weekly_days=5,
                           monthly_pct=10.0, monthly_days=21) is True
