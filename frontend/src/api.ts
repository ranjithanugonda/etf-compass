import type {
  DecisionData, DiagnosticData, EvidenceData,
  PositionResponse, StrategyParam, ETFAdmin,
} from './types'

const BASE = ''  // Vite proxies /api and /wiki to backend

async function get<T>(url: string): Promise<T> {
  const res = await fetch(`${BASE}${url}`)
  if (!res.ok) throw new Error(`${url}: ${res.status}`)
  return res.json()
}

export const api = {
  decision: () => get<DecisionData>('/api/dashboard/decision'),
  diagnostic: () => get<DiagnosticData>('/api/dashboard/diagnostic'),
  evidence: () => get<EvidenceData>('/api/dashboard/evidence'),
  positions: () => get<PositionResponse[]>('/api/positions'),
  login: (username: string, password: string) =>
    fetch(`${BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    }).then(r => r.json()) as Promise<{ access_token: string }>,

  getParams: () => get<StrategyParam[]>('/api/admin/strategy-params'),
  updateParam: (name: string, value: unknown) =>
    fetch(`${BASE}/api/admin/strategy-params/${name}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ param_value: value }),
    }).then(r => r.json()),

  getEtfs: () => get<ETFAdmin[]>('/api/admin/etfs'),
  toggleEtf: (symbol: string, active: boolean) =>
    fetch(`${BASE}/api/admin/etfs/${symbol}?active=${active}`, {
      method: 'PUT',
    }).then(r => r.json()),

  pause: () =>
    fetch(`${BASE}/api/admin/pause`, { method: 'POST' }).then(r => r.json()),
  resume: () =>
    fetch(`${BASE}/api/admin/resume`, { method: 'POST' }).then(r => r.json()),
}
