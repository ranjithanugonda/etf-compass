import { useEffect, useRef, useState } from 'react'
import {
  createChart, ColorType, CrosshairMode, CandlestickSeries, LineSeries, createSeriesMarkers,
  type CandlestickData, type Time, type SeriesMarker,
} from 'lightweight-charts'

interface Trade {
  action: string; entry_date: string; exit_date: string | null
  entry_price: number; exit_price: number | null
  pnl: number | null; pnl_pct: number | null; hold_days: number | null
  tranche_amount?: number
}

interface BacktestETF {
  symbol: string; total_trades: number; winning_trades: number; losing_trades: number
  win_rate: number; total_pnl: number; total_return_pct: number
  max_drawdown_pct: number; avg_hold_days: number; trades: Trade[]
}

interface OHLCBar {
  time: string; open: number; high: number; low: number; close: number
  ema21: number | null; ema60: number | null
}

interface Props {
  symbol: string
  onClose: () => void
}

export default function ETFDetailModal({ symbol, onClose }: Props) {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInst = useRef<ReturnType<typeof createChart> | null>(null)
  const [ohlc, setOHLC] = useState<OHLCBar[]>([])
  const [btData, setBtData] = useState<BacktestETF | null>(null)
  const [err, setErr] = useState('')
  const [tab, setTab] = useState<'chart' | 'trades'>('chart')

  useEffect(() => {
    Promise.all([
      fetch(`/api/ohlc/${symbol}?days=500`).then(r => r.json()),
      fetch(`/api/backtest/${symbol}`).then(r => r.json()),
    ]).then(([ohlcData, backtestData]) => {
      setOHLC(ohlcData)
      setBtData(backtestData)
    }).catch(e => setErr(e.message))
  }, [symbol])

  // Create chart only once when data arrives
  useEffect(() => {
    if (!chartRef.current || ohlc.length === 0 || btData === null) return

    const c = createChart(chartRef.current, {
      width: chartRef.current.clientWidth,
      height: 440,
      layout: {
        background: { type: ColorType.Solid, color: '#1a1d2e' },
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: '#2a2d3e' },
        horzLines: { color: '#2a2d3e' },
      },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: '#2a2d3e' },
      timeScale: {
        borderColor: '#2a2d3e',
        timeVisible: true,
        secondsVisible: false,
      },
    })
    chartInst.current = c

    const series = c.addSeries(CandlestickSeries, {
      upColor: '#10b981',
      downColor: '#ef4444',
      borderUpColor: '#10b981',
      borderDownColor: '#ef4444',
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    })

    const data: CandlestickData[] = ohlc.map(bar => ({
      time: bar.time as Time,
      open: bar.open,
      high: bar.high,
      low: bar.low,
      close: bar.close,
    }))
    series.setData(data)

    // EMA21 line
    const ema21Data = ohlc.filter(b => b.ema21 != null).map(b => ({ time: b.time as Time, value: b.ema21! }))
    if (ema21Data.length > 0) {
      const ema21Series = c.addSeries(LineSeries, {
        color: '#f59e0b', lineWidth: 1,
        priceLineVisible: false, lastValueVisible: false,
      })
      ema21Series.setData(ema21Data)
    }

    // EMA60 line
    const ema60Data = ohlc.filter(b => b.ema60 != null).map(b => ({ time: b.time as Time, value: b.ema60! }))
    if (ema60Data.length > 0) {
      const ema60Series = c.addSeries(LineSeries, {
        color: '#a78bfa', lineWidth: 1,
        priceLineVisible: false, lastValueVisible: false,
      })
      ema60Series.setData(ema60Data)
    }

    // Add markers from trades
    if (btData?.trades) {
      const markers: SeriesMarker<Time>[] = []
      const shapeMap: Record<string, 'arrowUp' | 'arrowDown' | 'circle'> = {
        entry: 'arrowUp', addon: 'circle',
        exit_profit: 'arrowDown', exit_time: 'arrowDown',
      }
      const colorMap: Record<string, string> = {
        entry: '#10b981', addon: '#f59e0b',
        exit_profit: '#3b82f6', exit_time: '#ef4444',
      }
      const labelMap: Record<string, string> = {
        entry: 'BUY', addon: 'ADD',
        exit_profit: 'SELL+', exit_time: 'SELL-',
      }

      btData.trades.forEach((t: Trade) => {
        markers.push({
          time: t.entry_date as Time,
          position: t.action.startsWith('exit') ? 'belowBar' : 'aboveBar',
          color: colorMap[t.action] || '#94a3b8',
          shape: shapeMap[t.action] || 'circle',
          text: labelMap[t.action] || t.action,
          size: 2,
        })
      })
      markers.sort((a, b) => String(a.time).localeCompare(String(b.time)))
      createSeriesMarkers(series, markers)
    }

    c.timeScale().fitContent()

    return () => {
      c.remove()
      chartInst.current = null
    }
  }, [ohlc, btData])

  const handleResize = () => {
    if (chartInst.current && chartRef.current) {
      chartInst.current.applyOptions({ width: chartRef.current.clientWidth })
    }
  }

  useEffect(() => {
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const isHolding = btData?.trades?.length
    && btData.trades[btData.trades.length - 1]?.exit_date === null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
         style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)' }}
         onClick={onClose}>
      <div className="rounded-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col"
           style={{ background: '#141720', border: '1px solid #2a2d3e' }}
           onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4"
             style={{ borderBottom: '1px solid #2a2d3e' }}>
          <div className="flex items-center gap-3">
            <div className="w-1 h-6 rounded-full bg-amber-500" />
            <h2 className="text-lg font-semibold text-white">{symbol}</h2>
            {isHolding && (
              <span className="px-2 py-0.5 text-xs font-medium rounded"
                    style={{ background: '#10b98115', color: '#10b981', border: '1px solid #10b98130' }}>
                Holding
              </span>
            )}
            {btData && (
              <span className="text-xs text-gray-500">
                {btData.total_trades} trades · {btData.win_rate.toFixed(0)}% win
                · P&L ₹{btData.total_pnl.toLocaleString()}
              </span>
            )}
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white text-xl leading-none">&times;</button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 px-6 py-2" style={{ borderBottom: '1px solid #2a2d3e' }}>
          {(['chart', 'trades'] as const).map(t => (
            <button key={t}
              onClick={() => setTab(t)}
              className="px-4 py-1.5 text-xs font-medium rounded capitalize transition-all"
              style={{
                background: tab === t ? '#3b82f6' : 'transparent',
                color: tab === t ? '#fff' : '#94a3b8',
              }}>
              {t === 'chart' ? 'Price Chart' : 'Trade Timeline'}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {err && <div className="text-red-400">{err}</div>}

          <div style={{ display: tab === 'chart' ? 'block' : 'none' }}>
            <div ref={chartRef} className="rounded-lg overflow-hidden" style={{ minHeight: 440 }} />
            {!ohlc.length && <div className="text-gray-500 text-sm mt-4 text-center">Loading chart data...</div>}
            <div className="flex items-center gap-4 mt-3 text-xs text-gray-500 justify-center">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500"/> Entry</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500"/> Add-on</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-500"/> Profit Exit</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500"/> Time Exit</span>
              <span className="text-gray-700">|</span>
              <span className="flex items-center gap-1"><span className="w-3 h-0.5 rounded" style={{background: '#f59e0b'}}/> EMA21</span>
              <span className="flex items-center gap-1"><span className="w-3 h-0.5 rounded" style={{background: '#a78bfa'}}/> EMA60</span>
            </div>
          </div>

          <div style={{ display: tab === 'trades' ? 'block' : 'none' }}>
            <div>
              {isHolding && (
                <div className="rounded-lg px-4 py-3 mb-4 text-sm"
                     style={{ background: '#10b98110', color: '#10b981', border: '1px solid #10b98120' }}>
                  Currently holding — position has not exited yet.
                </div>
              )}
              <div className="overflow-x-auto rounded-lg border" style={{ borderColor: '#2a2d3e' }}>
                <table className="w-full text-sm">
                  <thead>
                    <tr style={{ borderBottom: '1px solid #2a2d3e' }}>
                      <th className="p-3 text-xs font-medium text-gray-400 uppercase text-left">#</th>
                      <th className="p-3 text-xs font-medium text-gray-400 uppercase text-left">Action</th>
                      <th className="p-3 text-xs font-medium text-gray-400 uppercase text-left">Entry Date</th>
                      <th className="p-3 text-xs font-medium text-gray-400 uppercase text-right">Entry Price</th>
                      <th className="p-3 text-xs font-medium text-gray-400 uppercase text-right">Deployed</th>
                      <th className="p-3 text-xs font-medium text-gray-400 uppercase text-right">Units</th>
                      <th className="p-3 text-xs font-medium text-gray-400 uppercase text-left">Exit Date</th>
                      <th className="p-3 text-xs font-medium text-gray-400 uppercase text-right">Exit Price</th>
                      <th className="p-3 text-xs font-medium text-gray-400 uppercase text-right">Hold Days</th>
                      <th className="p-3 text-xs font-medium text-gray-400 uppercase text-right">P&L</th>
                      <th className="p-3 text-xs font-medium text-gray-400 uppercase text-right">Return %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(btData?.trades || []).map((t: Trade, i: number) => (
                      <tr key={i} style={{
                        borderBottom: '1px solid #2a2d3e',
                        background: i % 2 === 0 ? 'transparent' : '#1a1d2e',
                      }}>
                        <td className="p-3 text-gray-500">{i + 1}</td>
                        <td className="p-3">
                          <ActionBadge action={t.action} />
                        </td>
                        <td className="p-3 text-gray-300">{t.entry_date}</td>
                        <td className="p-3 text-gray-300 text-right">₹{t.entry_price.toFixed(2)}</td>
                        <td className="p-3 text-gray-300 text-right">
                          {t.tranche_amount ? `₹${t.tranche_amount.toLocaleString()}` : '-'}
                        </td>
                        <td className="p-3 text-gray-300 text-right">
                          {t.tranche_amount ? Math.round((t.tranche_amount || 0) / t.entry_price) : '-'}
                        </td>
                        <td className="p-3 text-gray-300">{t.exit_date || (
                          <span className="text-emerald-400 font-medium">Active</span>
                        )}</td>
                        <td className="p-3 text-gray-300 text-right">
                          {t.exit_price ? `₹${t.exit_price.toFixed(2)}` : '-'}
                        </td>
                        <td className="p-3 text-gray-300 text-right">
                          {t.hold_days != null ? `${t.hold_days}d` : '-'}
                        </td>
                        <td className="p-3 text-right font-medium"
                            style={{ color: (t.pnl || 0) >= 0 ? '#10b981' : '#ef4444' }}>
                          {t.pnl != null ? `₹${t.pnl.toFixed(0)}` : '-'}
                        </td>
                        <td className="p-3 text-right font-medium"
                            style={{ color: (t.pnl_pct || 0) >= 0 ? '#10b981' : '#ef4444' }}>
                          {t.pnl_pct != null ? `${t.pnl_pct.toFixed(1)}%` : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function ActionBadge({ action }: { action: string }) {
  const colors: Record<string, { bg: string; text: string }> = {
    entry: { bg: '#10b98115', text: '#10b981' },
    addon: { bg: '#f59e0b15', text: '#f59e0b' },
    exit_profit: { bg: '#3b82f615', text: '#3b82f6' },
    exit_time: { bg: '#ef444415', text: '#ef4444' },
  }
  const c = colors[action] || { bg: '#64748b15', text: '#64748b' }
  return (
    <span className="px-2 py-0.5 rounded text-xs font-medium border"
          style={{ background: c.bg, color: c.text, borderColor: c.text + '30' }}>
      {action.replace('_', ' ')}
    </span>
  )
}
