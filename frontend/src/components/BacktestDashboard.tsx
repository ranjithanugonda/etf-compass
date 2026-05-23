import { useEffect, useRef, useState } from 'react'
import { createChart, ColorType, LineSeries } from 'lightweight-charts'
import ETFDetailModal from './ETFDetailModal'

interface PortfolioPoint {
  month: string; month_label: string
  etfs_held: number; capital_deployed: number; capital_available: number
}

interface Holding {
  symbol: string; entry_date: string; entry_price: number
  capital_deployed?: number
  last_addon_date?: string; last_addon_price?: number
  action: string
}

interface BacktestSummary {
  etfs_tested: number; total_trades: number
  winning_trades: number; losing_trades: number
  win_rate: number; total_pnl: number
  total_corpus?: number; total_invested?: number; available_capital?: number
  start_date?: string
  currently_holding?: Holding[]
  etfs: BacktestETF[]
  status?: string
  message?: string
}

interface BacktestETF {
  symbol: string; total_trades: number
  winning_trades: number; losing_trades: number
  win_rate: number; total_pnl: number
  total_return_pct: number; max_drawdown_pct: number
  avg_hold_days: number
}

function fmtDate(d: Date): string {
  return d.toISOString().split('T')[0]
}

export default function BacktestDashboard() {
  const [data, setData] = useState<BacktestSummary | null>(null)
  const [err, setErr] = useState('')
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null)

  // Configurable inputs
  const today = new Date()
  const twoYearsAgo = new Date(today)
  twoYearsAgo.setFullYear(today.getFullYear() - 2)
  const [startDate, setStartDate] = useState(fmtDate(twoYearsAgo))
  const [corpus, setCorpus] = useState('15000000')
  const [running, setRunning] = useState(false)
  const [runMsg, setRunMsg] = useState('')
  const [history, setHistory] = useState<PortfolioPoint[]>([])
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInst = useRef<ReturnType<typeof createChart> | null>(null)

  const loadData = () => {
    fetch('/api/backtest/summary')
      .then(r => r.json())
      .then(d => {
        setData(d)
        if (d.total_corpus) setCorpus(String(d.total_corpus))
        if (d.start_date) setStartDate(d.start_date)
      })
      .catch(e => setErr(e.message))
    fetch('/api/backtest/portfolio-history')
      .then(r => r.json()).then(setHistory).catch(() => {})
  }

  useEffect(loadData, [])

  // Portfolio allocation chart
  useEffect(() => {
    if (!chartRef.current || history.length === 0) return
    if (chartInst.current) {
      chartInst.current.remove()
      chartInst.current = null
    }

    const c = createChart(chartRef.current, {
      width: chartRef.current.clientWidth,
      height: 280,
      layout: {
        background: { type: ColorType.Solid, color: '#1a1d2e' },
        textColor: '#94a3b8',
      },
      grid: { vertLines: { color: '#2a2d3e' }, horzLines: { color: '#2a2d3e' } },
      rightPriceScale: { borderColor: '#2a2d3e', scaleMargins: { top: 0.1, bottom: 0.1 } },
      timeScale: { borderColor: '#2a2d3e', timeVisible: false },
    })
    chartInst.current = c

    // Capital deployed line (left axis, blue)
    const capitalSeries = c.addSeries(LineSeries, {
      color: '#3b82f6', lineWidth: 2,
      priceFormat: { type: 'custom', formatter: (p: number) => `₹${(p / 100000).toFixed(1)}L` },
    })
    capitalSeries.setData(history.map(d => ({ time: d.month, value: d.capital_deployed })))

    // ETFs held line (right axis, green)
    const etfSeries = c.addSeries(LineSeries, {
      color: '#10b981', lineWidth: 2,
      priceFormat: { type: 'custom', formatter: (p: number) => `${p.toFixed(0)} ETFs` },
      priceScaleId: 'etfs',
    })
    c.priceScale('etfs').applyOptions({
      scaleMargins: { top: 0, bottom: 0 },
      borderColor: '#2a2d3e',
    })
    etfSeries.setData(history.map(d => ({ time: d.month, value: d.etfs_held })))

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
  }, [history])

  const runBacktest = async () => {
    setRunning(true)
    setRunMsg('Running backtest...')
    try {
      const res = await fetch('/api/admin/run-backtest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          start_date: startDate,
          total_corpus: Number(corpus),
        }),
      })
      const result = await res.json()
      if (!res.ok) {
        setRunMsg(`Error: ${result.detail || 'Failed'}`)
      } else {
        setRunMsg(`Done — ${result.etfs_tested} ETFs, ${result.total_trades} trades, ${result.total_pnl}`)
        loadData()
      }
    } catch {
      setRunMsg('Network error')
    }
    setRunning(false)
  }

  if (err) return <div className="text-red-400 p-4">Error: {err}</div>
  if (!data) return <div className="text-gray-400 p-4">Loading...</div>

  const holdings = data.currently_holding || []
  const startedEtfs = data.etfs.filter(e => e.total_trades > 0 || holdings.some(h => h.symbol === e.symbol))

  const borderColor = '#2a2d3e'
  const thClass = 'p-3 text-xs font-medium text-gray-400 uppercase tracking-wider'
  const inputStyle: React.CSSProperties = {
    background: '#141720', borderColor: '#2a2d3e', color: '#e2e8f0',
  }

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-1 h-6 rounded-full bg-amber-500" />
        <h1 className="text-xl font-semibold text-white">Backtest Results</h1>
        {data.start_date && (
          <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded">
            Since {data.start_date}
          </span>
        )}
      </div>

      {/* Config bar */}
      <div className="flex flex-wrap items-end gap-3 mb-4 rounded-xl border p-4"
           style={{ borderColor, background: '#1a1d2e' }}>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Start Date</label>
          <input
            type="date"
            value={startDate}
            onChange={e => setStartDate(e.target.value)}
            className="rounded-lg px-3 py-1.5 text-sm border focus:outline-none"
            style={inputStyle}
          />
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Total Corpus (₹)</label>
          <input
            type="number"
            value={corpus}
            onChange={e => setCorpus(e.target.value)}
            className="rounded-lg px-3 py-1.5 text-sm border focus:outline-none w-40"
            style={inputStyle}
          />
        </div>
        <button
          onClick={runBacktest}
          disabled={running}
          className="px-5 py-1.5 rounded-lg text-sm font-medium text-white transition-colors disabled:opacity-50"
          style={{ background: '#7c3aed' }}>
          {running ? 'Running...' : 'Run Backtest'}
        </button>
        {runMsg && (
          <span className="text-xs font-mono" style={{ color: runMsg.startsWith('Error') ? '#ef4444' : '#10b981' }}>
            {runMsg}
          </span>
        )}
      </div>

      {/* Portfolio Allocation Chart */}
      <div className="rounded-xl border mb-6 overflow-hidden" style={{ borderColor, background: '#1a1d2e' }}>
        <div className="flex items-center justify-between px-4 py-3" style={{ borderBottom: `1px solid ${borderColor}` }}>
          <h2 className="text-sm font-semibold text-gray-200">Portfolio Allocation Over Time</h2>
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span className="flex items-center gap-1"><span className="w-3 h-0.5 rounded" style={{background:'#3b82f6'}}/> Capital Deployed</span>
            <span className="flex items-center gap-1"><span className="w-3 h-0.5 rounded" style={{background:'#10b981'}}/> ETFs Held</span>
          </div>
        </div>
        <div className="p-1">
          <div ref={chartRef} style={{ minHeight: 280 }} />
        </div>
      </div>

      {/* Aggregate cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
        <StatCard label="Corpus" value={`₹${((data.total_corpus || 15000000) / 100000).toFixed(0)} L`} />
        <StatCard label="Invested" value={`₹${((data.total_invested || 0) / 100000).toFixed(2)} L`}
          color="#3b82f6" />
        <StatCard label="Available" value={`₹${((data.available_capital || 0) / 100000).toFixed(2)} L`}
          color="#10b981" />
        <StatCard label="Utilization" value={`${(((data.total_invested || 0) / (data.total_corpus || 1)) * 100).toFixed(1)}%`}
          color="#f59e0b" />
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        <StatCard label="ETFs Holding" value={String(holdings.length)} color="#60a5fa" />
        <StatCard label="ETFs Started" value={String(startedEtfs.length)} />
        <StatCard label="Win Rate" value={`${data.win_rate}%`}
          color={data.win_rate >= 50 ? '#10b981' : '#ef4444'} />
        <StatCard label="Total P&L" value={`₹${(data.total_pnl / 100_000).toFixed(2)} L`}
          color={data.total_pnl >= 0 ? '#10b981' : '#ef4444'} />
      </div>

      {/* Currently Holding */}
      {holdings.length > 0 && (
        <div className="rounded-xl border overflow-hidden mb-6" style={{ borderColor, background: '#1a1d2e' }}>
          <div className="flex items-center justify-between px-4 py-3" style={{ borderBottom: `1px solid ${borderColor}` }}>
            <h2 className="text-sm font-semibold text-emerald-400">Currently Holding</h2>
            <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded">{holdings.length}</span>
          </div>
          <table className="w-full">
            <thead>
              <tr style={{ borderBottom: `1px solid ${borderColor}` }}>
                <th className={thClass} style={{ textAlign: 'left' }}>ETF</th>
                <th className={thClass} style={{ textAlign: 'left' }}>Entry Date</th>
                <th className={thClass} style={{ textAlign: 'right' }}>Entry Price</th>
                <th className={thClass} style={{ textAlign: 'right' }}>Capital</th>
                <th className={thClass} style={{ textAlign: 'left' }}>Last Addon</th>
              </tr>
            </thead>
            <tbody>
              {holdings.map((h, i) => (
                <tr key={h.symbol} style={{
                  borderBottom: `1px solid ${borderColor}`,
                  background: i % 2 === 0 ? 'transparent' : '#141720',
                }}>
                  <td className="p-3 text-sm font-medium text-emerald-400">{h.symbol}</td>
                  <td className="p-3 text-sm text-gray-300">{h.entry_date}</td>
                  <td className="p-3 text-sm text-gray-300" style={{ textAlign: 'right' }}>
                    ₹{h.entry_price.toFixed(2)}
                  </td>
                  <td className="p-3 text-sm text-gray-300" style={{ textAlign: 'right' }}>
                    {h.capital_deployed ? `₹${h.capital_deployed.toLocaleString()}` : '—'}
                  </td>
                  <td className="p-3 text-sm text-gray-400">
                    {h.last_addon_date ? `${h.last_addon_date} @ ₹${h.last_addon_price?.toFixed(2)}` : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Per-ETF table */}
      <div className="rounded-xl border overflow-hidden" style={{ borderColor, background: '#1a1d2e' }}>
        <div className="flex items-center px-4 py-3" style={{ borderBottom: `1px solid ${borderColor}` }}>
          <h2 className="text-sm font-semibold text-gray-200">Per-ETF Performance</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr style={{ borderBottom: `1px solid ${borderColor}` }}>
                <th className={thClass} style={{ textAlign: 'left' }}>ETF</th>
                <th className={thClass} style={{ textAlign: 'right' }}>Trades</th>
                <th className={thClass} style={{ textAlign: 'right' }}>Win Rate</th>
                <th className={thClass} style={{ textAlign: 'right' }}>P&L</th>
                <th className={thClass} style={{ textAlign: 'right' }}>Return %</th>
                <th className={thClass} style={{ textAlign: 'right' }}>Max DD %</th>
                <th className={thClass} style={{ textAlign: 'right' }}>Avg Hold (d)</th>
              </tr>
            </thead>
            <tbody>
              {data.etfs.filter(e => e.total_trades > 0 || holdings.some(h => h.symbol === e.symbol)).map((e, i) => (
                <tr key={e.symbol}
                  style={{
                    borderBottom: `1px solid ${borderColor}`,
                    background: i % 2 === 0 ? 'transparent' : '#141720',
                  }}>
                  <td className="p-3 text-sm font-medium" style={{ color: '#e2e8f0' }}>
                    <button
                      onClick={() => setSelectedSymbol(e.symbol)}
                      className="text-blue-400 hover:text-blue-300 hover:underline cursor-pointer text-left">
                      {e.symbol}
                    </button>
                  </td>
                  <td className="p-3 text-sm text-gray-300" style={{ textAlign: 'right' }}>
                    {e.total_trades}
                  </td>
                  <td className="p-3 text-sm font-medium" style={{
                    textAlign: 'right',
                    color: e.win_rate >= 50 ? '#10b981' : '#ef4444',
                  }}>
                    {e.total_trades > 0 ? `${e.win_rate.toFixed(0)}%` : '—'}
                  </td>
                  <td className="p-3 text-sm font-medium" style={{
                    textAlign: 'right',
                    color: e.total_pnl >= 0 ? '#10b981' : '#ef4444',
                  }}>
                    ₹{e.total_pnl.toLocaleString()}
                  </td>
                  <td className="p-3 text-sm font-medium" style={{
                    textAlign: 'right',
                    color: e.total_return_pct >= 0 ? '#10b981' : '#ef4444',
                  }}>
                    {e.total_return_pct.toFixed(1)}%
                  </td>
                  <td className="p-3 text-sm" style={{
                    textAlign: 'right',
                    color: e.max_drawdown_pct > 30 ? '#ef4444' : '#94a3b8',
                  }}>
                    {e.max_drawdown_pct.toFixed(1)}%
                  </td>
                  <td className="p-3 text-sm text-gray-400" style={{ textAlign: 'right' }}>
                    {Math.round(e.avg_hold_days)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {selectedSymbol && (
        <ETFDetailModal
          symbol={selectedSymbol}
          onClose={() => setSelectedSymbol(null)}
        />
      )}
    </div>
  )
}

function StatCard({ label, value, color }: {
  label: string; value: string; color?: string
}) {
  return (
    <div style={{ background: '#1a1d2e', borderColor: '#2a2d3e' }}
         className="rounded-xl border p-4">
      <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">{label}</div>
      <div className="text-lg font-bold" style={{ color: color || '#e2e8f0' }}>{value}</div>
    </div>
  )
}
