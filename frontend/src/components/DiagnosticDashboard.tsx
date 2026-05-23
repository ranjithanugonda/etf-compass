import { useEffect, useRef, useState } from 'react'
import {
  createChart, ColorType, LineSeries,
} from 'lightweight-charts'
import ETFDetailModal from './ETFDetailModal'

interface MonthlyPoint {
  month: string; month_label: string; pnl: number; roi_pct: number
  new_positions: number; addons: number; profit_exits: number; time_exits: number
}

export default function DiagnosticDashboard() {
  const [data, setData] = useState<MonthlyPoint[]>([])
  const [err, setErr] = useState('')
  const [symbol, setSymbol] = useState('ALL')
  const [source, setSource] = useState<'backtest' | 'live'>('backtest')
  const [etfList, setEtfList] = useState<string[]>([])
  const [modalSymbol, setModalSymbol] = useState<string | null>(null)
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInst = useRef<ReturnType<typeof createChart> | null>(null)
  const [chartKey, setChartKey] = useState(0)  // force chart recreate on filter change

  // Load ETF list from backtest
  useEffect(() => {
    fetch('/api/backtest/summary')
      .then(r => r.json())
      .then(d => {
        if (d.etfs) setEtfList(d.etfs.map((e: { symbol: string }) => e.symbol))
      }).catch(() => {})
  }, [])

  // Load data when filter changes
  useEffect(() => {
    const params = new URLSearchParams({ symbol, source })
    fetch(`/api/dashboard/diagnostic/data?${params}`)
      .then(r => r.json()).then(d => {
        setData(d)
        setChartKey(k => k + 1)  // force chart recreate
        chartInst.current = null  // reset chart ref
      })
      .catch(e => setErr(e.message))
  }, [symbol, source])

  // ROI line chart
  useEffect(() => {
    if (!chartRef.current || data.length === 0 || chartInst.current) return

    const c = createChart(chartRef.current, {
      width: chartRef.current.clientWidth,
      height: 300,
      layout: {
        background: { type: ColorType.Solid, color: '#1a1d2e' },
        textColor: '#94a3b8',
      },
      grid: { vertLines: { color: '#2a2d3e' }, horzLines: { color: '#2a2d3e' } },
      rightPriceScale: { borderColor: '#2a2d3e', scaleMargins: { top: 0.15, bottom: 0.15 } },
      timeScale: { borderColor: '#2a2d3e', timeVisible: false },
    })
    chartInst.current = c

    const roiSeries = c.addSeries(LineSeries, {
      color: '#3b82f6', lineWidth: 2,
      priceFormat: { type: 'custom', formatter: (p: number) => `${p.toFixed(2)}%` },
    })
    roiSeries.setData(data.map(d => ({ time: d.month, value: d.roi_pct })))

    const pnlSeries = c.addSeries(LineSeries, {
      color: '#10b98133', lineWidth: 1,
      priceFormat: { type: 'custom', formatter: (p: number) => `₹${p.toFixed(0)}` },
      priceScaleId: 'pnl',
    })
    c.priceScale('pnl').applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
      visible: false,
    })
    pnlSeries.setData(data.map(d => ({ time: d.month, value: d.pnl })))

    c.timeScale().fitContent()

    const handleResize = () => {
      if (chartInst.current && chartRef.current) {
        chartInst.current.applyOptions({ width: chartRef.current.clientWidth })
      }
    }
    window.addEventListener('resize', handleResize)
    return () => {
      window.removeEventListener('resize', handleResize)
      c.remove(); chartInst.current = null
    }
  }, [data, chartKey])

  if (err) return <div className="text-red-400 p-4">Error: {err}</div>

  const reversed = [...data].reverse()
  const borderColor = '#2a2d3e'
  const thClass = 'p-3 text-xs font-medium text-gray-400 uppercase tracking-wider'
  const tdClass = 'p-3 text-sm text-gray-300'

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-1 h-6 rounded-full bg-purple-500" />
        <h1 className="text-xl font-semibold text-white">Diagnostic Dashboard</h1>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 mb-4">
        {/* Source toggle */}
        <div className="flex gap-0.5 rounded-lg p-0.5" style={{ background: '#1a1d2e', border: '1px solid #2a2d3e' }}>
          {(['backtest', 'live'] as const).map(s => (
            <button key={s}
              onClick={() => setSource(s)}
              className="px-3 py-1 text-xs font-medium rounded capitalize transition-all"
              style={{
                background: source === s ? '#3b82f6' : 'transparent',
                color: source === s ? '#fff' : '#94a3b8',
              }}>
              {s}
            </button>
          ))}
        </div>

        {/* ETF Filter */}
        <select
          value={symbol}
          onChange={e => setSymbol(e.target.value)}
          className="text-xs rounded-lg px-3 py-1.5 border focus:outline-none"
          style={{ background: '#1a1d2e', borderColor: '#2a2d3e', color: '#e2e8f0' }}>
          <option value="ALL">All ETFs</option>
          {etfList.map(sym => (
            <option key={sym} value={sym}>{sym}</option>
          ))}
        </select>

        <span className="text-xs text-gray-600">
          {symbol === 'ALL' ? 'Aggregate across all ETFs' : `Filtered: ${symbol}`} &middot; {source === 'backtest' ? '2-year simulation' : 'Live trades'}
        </span>
      </div>

      {/* ROI Chart */}
      <div className="rounded-xl border mb-6 overflow-hidden" style={{ borderColor, background: '#1a1d2e' }}>
        <div className="flex items-center justify-between px-4 py-3" style={{ borderBottom: `1px solid ${borderColor}` }}>
          <h2 className="text-sm font-semibold text-gray-200">Monthly ROI — 12 Months</h2>
          <span className="text-xs text-gray-500">% return on total corpus</span>
        </div>
        <div className="p-1">
          <div ref={chartRef} key={chartKey} style={{ minHeight: 300 }} />
        </div>
      </div>

      {/* Activity Table */}
      <div className="overflow-x-auto rounded-xl border" style={{ borderColor, background: '#1a1d2e' }}>
        <div className="flex items-center justify-between px-4 py-3" style={{ borderBottom: `1px solid ${borderColor}` }}>
          <h2 className="text-sm font-semibold text-gray-200">Monthly Activity</h2>
        </div>
        <table className="w-full">
          <thead>
            <tr style={{ borderBottom: `1px solid ${borderColor}` }}>
              <th className={thClass} style={{ textAlign: 'left' }}>Month</th>
              <th className={thClass} style={{ textAlign: 'right' }}>New</th>
              <th className={thClass} style={{ textAlign: 'right' }}>Add-ons</th>
              <th className={thClass} style={{ textAlign: 'right' }}>Profit Exit</th>
              <th className={thClass} style={{ textAlign: 'right' }}>Time Exit</th>
              <th className={thClass} style={{ textAlign: 'right' }}>P&L</th>
            </tr>
          </thead>
          <tbody>
            {reversed.map((m, i) => (
              <tr key={m.month_label}
                style={{
                  borderBottom: `1px solid ${borderColor}`,
                  background: i % 2 === 0 ? 'transparent' : '#141720',
                }}>
                <td className={tdClass} style={{ fontWeight: 500, color: '#e2e8f0' }}>{m.month_label}</td>
                {[m.new_positions, m.addons, m.profit_exits, m.time_exits].map((val, ci) => {
                  const clickable = symbol !== 'ALL' && val > 0
                  return (
                    <td key={ci} className={tdClass} style={{ textAlign: 'right' }}>
                      {clickable ? (
                        <button onClick={() => setModalSymbol(symbol)}
                          className="text-blue-400 hover:text-blue-300 hover:underline cursor-pointer">
                          {val}
                        </button>
                      ) : (val || '-')}
                    </td>
                  )
                })}
                <td className={tdClass} style={{
                  textAlign: 'right', fontWeight: 600,
                  color: m.pnl >= 0 ? '#10b981' : '#ef4444',
                }}>
                  {m.pnl !== 0 ? `₹${m.pnl.toLocaleString('en-IN', { maximumFractionDigits: 0 })}` : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {modalSymbol && (
        <ETFDetailModal
          symbol={modalSymbol}
          onClose={() => setModalSymbol(null)}
        />
      )}
    </div>
  )
}
