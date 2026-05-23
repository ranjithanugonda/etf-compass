export interface DecisionData {
  ytd_roi_pct: number
  expected_roi_pct: number
  avg_duration_months: number
  expected_holding_months: number
  capital_utilized_pct: number
  total_corpus: number
}

export interface MonthlyActivity {
  month: string
  new_positions: number
  addons: number
  profit_exits: number
  time_exits: number
}

export interface DiagnosticData {
  rolling_12_months: MonthlyActivity[]
}

export interface EvidenceData {
  positions: {
    symbol: string; status: string; tranches_used: number
    capital_deployed: number; wac: number | null; entered_at: string | null
  }[]
  recent_trades: {
    id: number; action: string; tranche_number: number
    quantity: number; fill_price: number | null; filled_at: string | null
  }[]
  wiki_pages: string[]
}

export interface PositionResponse {
  symbol: string; name: string; category: string; status: string
  tranches_used: number; total_capital_deployed: number; total_units: number
  last_buy_price: number | null; weighted_avg_cost: number | null
  unrealized_pnl: number | null; trend_regime: string | null
  entered_at: string | null; days_held: number | null
}

export interface StrategyParam {
  param_name: string
  param_value: unknown
  description: string
}

export interface ETFAdmin {
  symbol: string; name: string; category: string; active: boolean
}
