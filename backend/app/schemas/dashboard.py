"""Pydantic response models for dashboard endpoints."""

from pydantic import BaseModel


class DecisionDashboard(BaseModel):
    ytd_roi_pct: float
    expected_roi_pct: float
    avg_duration_months: float
    expected_holding_months: float
    capital_utilized_pct: float
    total_corpus: float


class MonthlyActivity(BaseModel):
    month: str  # YYYY-MM
    new_positions: int
    addons: int
    profit_exits: int
    time_exits: int


class DiagnosticDashboard(BaseModel):
    rolling_12_months: list[MonthlyActivity]


class EvidenceItem(BaseModel):
    symbol: str
    action: str
    date: str
    amount: float
    wiki_link: str


class EvidenceDashboard(BaseModel):
    positions: list[dict[str, object]]
    recent_trades: list[dict[str, object]]
    wiki_pages: list[str]
