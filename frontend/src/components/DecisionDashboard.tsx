import { useEffect, useState } from 'react'
import { api } from '../api'
import type { DecisionData } from '../types'

export default function DecisionDashboard() {
  const [data, setData] = useState<DecisionData | null>(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    api.decision().then(setData).catch(e => setErr(e.message))
  }, [])

  if (err) return <div className="text-red-400 p-4">Error: {err}</div>
  if (!data) return <div className="text-gray-400 p-4">Loading...</div>

  const roiOk = data.ytd_roi_pct >= data.expected_roi_pct
  const durOk = data.avg_duration_months <= data.expected_holding_months

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-1 h-6 rounded-full bg-blue-500" />
        <h1 className="text-xl font-semibold text-white">Decision Dashboard</h1>
        <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded">
          Last scan: today
        </span>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Card label="YTD ROI" value={`${data.ytd_roi_pct}%`}
          sub={`Expected: ${data.expected_roi_pct}%`}
          ok={roiOk} okLabel="Above target" badLabel="Below target" />
        <Card label="Avg Duration" value={`${data.avg_duration_months} mo`}
          sub={`Target: ≤ ${data.expected_holding_months} mo`}
          ok={durOk} okLabel="Within target" badLabel="Exceeded" />
        <Card label="Capital Utilized" value={`${data.capital_utilized_pct}%`}
          sub={`of ${fmtCr(data.total_corpus)}`}
          ok={true} okLabel="" badLabel="" neutral />
        <Card label="Total Corpus" value={fmtCr(data.total_corpus)}
          sub="Available capital"
          ok={true} okLabel="" badLabel="" neutral />
      </div>
    </div>
  )
}

function Card({ label, value, sub, ok, okLabel, badLabel, neutral }: {
  label: string; value: string; sub: string; ok: boolean
  okLabel: string; badLabel: string; neutral?: boolean
}) {
  const statusColor = neutral ? '#60a5fa' : ok ? '#10b981' : '#ef4444'
  return (
    <div style={{ background: '#1a1d2e', borderColor: '#2a2d3e' }}
         className="rounded-xl border p-5">
      <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
        {label}
      </div>
      <div className="text-2xl font-bold text-white mb-1" style={{ color: neutral ? '#e2e8f0' : statusColor }}>
        {value}
      </div>
      <div className="text-xs text-gray-600">{sub}</div>
      {!neutral && (
        <div className="flex items-center gap-1.5 mt-3">
          <div className="w-1.5 h-1.5 rounded-full" style={{ background: statusColor }} />
          <span className="text-xs font-medium" style={{ color: statusColor }}>
            {ok ? okLabel : badLabel}
          </span>
        </div>
      )}
    </div>
  )
}

function fmtCr(n: number) {
  if (n >= 1_00_00_000) return `₹${(n / 1_00_00_000).toFixed(2)} Cr`
  if (n >= 1_00_000) return `₹${(n / 1_00_000).toFixed(1)} L`
  return `₹${n.toLocaleString()}`
}
