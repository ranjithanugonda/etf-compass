from backend.app.strategy.models import TrendRegime
from backend.app.strategy.trend import determine_trend


def test_strong_trend() -> None:
    result = determine_trend(close=110.0, ema21=105.0, ema60=95.0)
    assert result == TrendRegime.STRONG


def test_neutral_trend_price_below_ema21() -> None:
    result = determine_trend(close=100.0, ema21=105.0, ema60=95.0)
    assert result == TrendRegime.NEUTRAL


def test_neutral_trend_ema21_below_ema60() -> None:
    result = determine_trend(close=100.0, ema21=90.0, ema60=95.0)
    assert result == TrendRegime.NEUTRAL


def test_weak_trend() -> None:
    result = determine_trend(close=90.0, ema21=105.0, ema60=95.0)
    assert result == TrendRegime.WEAK


def test_close_equals_ema60_weak() -> None:
    result = determine_trend(close=95.0, ema21=105.0, ema60=95.0)
    assert result == TrendRegime.WEAK


def test_close_equals_ema21_strong_if_emas_ordered() -> None:
    result = determine_trend(close=105.0, ema21=105.0, ema60=95.0)
    assert result == TrendRegime.NEUTRAL  # close not strictly > ema21


def test_none_ema21_returns_weak() -> None:
    result = determine_trend(close=100.0, ema21=None, ema60=95.0)
    assert result == TrendRegime.WEAK


def test_none_ema60_returns_weak() -> None:
    result = determine_trend(close=100.0, ema21=105.0, ema60=None)
    assert result == TrendRegime.WEAK


def test_both_none_returns_weak() -> None:
    result = determine_trend(close=100.0, ema21=None, ema60=None)
    assert result == TrendRegime.WEAK
