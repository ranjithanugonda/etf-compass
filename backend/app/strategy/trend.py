"""Trend regime classifier based on EMA21 and EMA60."""

from backend.app.strategy.models import TrendRegime


def determine_trend(close: float, ema21: float | None, ema60: float | None) -> TrendRegime:
    """Classify trend regime from price and EMA values.

    PRD §5:
      - Strong:  close > EMA21 AND EMA21 > EMA60
      - Neutral: close > EMA60 but not Strong
      - Weak:    close <= EMA60 (or insufficient data)
    """
    if ema21 is None or ema60 is None:
        return TrendRegime.WEAK

    if close > ema21 and ema21 > ema60:
        return TrendRegime.STRONG

    if close > ema60:
        return TrendRegime.NEUTRAL

    return TrendRegime.WEAK
