"""Pure dataclasses for the strategy engine. No database dependency."""

import enum
from dataclasses import dataclass
from datetime import date


class TrendRegime(enum.StrEnum):
    STRONG = "strong"
    NEUTRAL = "neutral"
    WEAK = "weak"


class SignalAction(enum.StrEnum):
    ENTRY = "entry"
    ADDON = "addon"
    EXIT_PROFIT = "exit_profit"
    EXIT_TIME = "exit_time"
    EXIT_SL = "exit_sl"


@dataclass
class OHLCBar:
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    ema21: float | None = None
    ema60: float | None = None


@dataclass
class PositionState:
    status: str = "flat"  # "active" | "flat"
    tranches_used: int = 0
    total_capital_deployed: float = 0.0
    total_units: float = 0.0
    last_buy_price: float | None = None
    weighted_avg_cost: float | None = None
    entered_at: date | None = None
    last_addon_date: date | None = None

    @property
    def is_active(self) -> bool:
        return self.status == "active"


@dataclass
class StrategyParams:
    total_corpus: float = 15_000_000
    initial_tranche: float = 300_000
    second_tranche: float = 200_000
    third_tranche: float = 150_000
    addon_tranche: float = 100_000
    max_position_size: float = 1_250_000
    max_tranches: int = 9
    profit_target_pct: float = 5.0
    stop_loss_pct: float = 5.0
    time_stop_months: int = 4
    addon_threshold_pct: float = 2.5
    addon_duration_days: int = 7
    pullback_weekly_pct: float = 2.5
    pullback_weekly_days: int = 5
    pullback_monthly_pct: float = 5.0
    pullback_monthly_days: int = 21


@dataclass
class Signal:
    symbol: str
    action: SignalAction
    tranche_amount: float
    limit_price: float
    reason: str
