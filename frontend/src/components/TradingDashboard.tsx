import { useEffect, useState } from 'react'

interface Position {
  id: number; etf_symbol: string; status: string
  total_capital_deployed: number; total_units: number
  tranches_used: number; weighted_avg_cost: number | null
  last_buy_price: number | null; entered_at: string | null
}

interface Trade {
  id: number; symbol: string; action: string
  tranche_number: number; quantity: number
  limit_price: number; fill_price: number | null
  order_status: string; filled_at: string | null
}

const ACTIONS = [
  { value: 'entry', label: 'Entry (New Position)', color: '#10b981' },
  { value: 'addon', label: 'Add-on (DCA)', color: '#f59e0b' },
  { value: 'exit_profit', label: 'Exit (Profit)', color: '#3b82f6' },
  { value: 'exit_time', label: 'Exit (Time Stop)', color: '#ef4444' },
]

export default function TradingDashboard() {
  const [positions, setPositions] = useState<Position[]>([])
  const [recentTrades, setRecentTrades] = useState<Trade[]>([])
  const [etfList, setEtfList] = useState<string[]>([])
  const [symbol, setSymbol] = useState('')
  const [action, setAction] = useState('entry')
  const [quantity, setQuantity] = useState('')
  const [limitPrice, setLimitPrice] = useState('')
  const [msg, setMsg] = useState('')
  const [msgType, setMsgType] = useState<'success' | 'error'>('success')

  const loadData = () => {
    fetch('/api/positions').then(r => r.json()).then(setPositions).catch(() => {})
    fetch('/api/trades/recent').then(r => r.json()).then(setRecentTrades).catch(() => {})
    fetch('/api/backtest/summary').then(r => r.json()).then(d => {
      if (d.etfs) setEtfList(d.etfs.map((e: { symbol: string }) => e.symbol))
    }).catch(() => {})
  }

  useEffect(loadData, [])

  const activePositions = positions.filter(p => p.status === 'active')

  const placeTrade = async () => {
    if (!symbol || !quantity || !limitPrice) {
      setMsg('All fields required'); setMsgType('error'); return
    }
    try {
      const res = await fetch('/api/trades/place', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol, action,
          quantity: Number(quantity),
          limit_price: Number(limitPrice),
        }),
      })
      if (!res.ok) {
        const err = await res.json()
        setMsg(err.detail || 'Trade failed'); setMsgType('error')
        return
      }
      const trade = await res.json()
      setMsg(`${trade.action} ${trade.quantity} units of ${trade.symbol} @ ₹${trade.limit_price}`)
      setMsgType('success')
      setQuantity('')
      setLimitPrice('')
      loadData()
    } catch {
      setMsg('Network error'); setMsgType('error')
    }
  }

  const borderColor = '#2a2d3e'
  const thClass = 'p-3 text-xs font-medium text-gray-400 uppercase tracking-wider'
  const tdClass = 'p-3 text-sm text-gray-300'
  const inputStyle: React.CSSProperties = {
    background: '#141720', borderColor: '#2a2d3e', color: '#e2e8f0',
  }

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-1 h-6 rounded-full bg-cyan-500" />
        <h1 className="text-xl font-semibold text-white">Trading</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trade Form */}
        <div>
          <div className="rounded-xl border overflow-hidden mb-4" style={{ borderColor, background: '#1a1d2e' }}>
            <div className="px-4 py-3" style={{ borderBottom: `1px solid ${borderColor}` }}>
              <h2 className="text-sm font-semibold text-gray-200">Place Trade</h2>
            </div>
            <div className="p-4 space-y-4">
              {/* ETF Selector */}
              <div>
                <label className="text-xs text-gray-500 mb-1.5 block">ETF</label>
                <select
                  value={symbol}
                  onChange={e => setSymbol(e.target.value)}
                  className="w-full rounded-lg px-3 py-2 text-sm border focus:outline-none"
                  style={inputStyle}>
                  <option value="">Select ETF...</option>
                  {etfList.map(s => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>

              {/* Action */}
              <div>
                <label className="text-xs text-gray-500 mb-1.5 block">Action</label>
                <div className="grid grid-cols-2 gap-2">
                  {ACTIONS.map(a => (
                    <button key={a.value}
                      onClick={() => setAction(a.value)}
                      className="px-3 py-2 rounded-lg text-xs font-medium border transition-all"
                      style={{
                        background: action === a.value ? a.color + '18' : 'transparent',
                        color: action === a.value ? a.color : '#94a3b8',
                        borderColor: action === a.value ? a.color + '40' : borderColor,
                      }}>
                      {a.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Quantity & Price */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-gray-500 mb-1.5 block">Quantity (units)</label>
                  <input
                    type="number"
                    value={quantity}
                    onChange={e => setQuantity(e.target.value)}
                    placeholder="100"
                    className="w-full rounded-lg px-3 py-2 text-sm border focus:outline-none focus:border-blue-500"
                    style={inputStyle}
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 mb-1.5 block">Limit Price (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={limitPrice}
                    onChange={e => setLimitPrice(e.target.value)}
                    placeholder="250.00"
                    className="w-full rounded-lg px-3 py-2 text-sm border focus:outline-none focus:border-blue-500"
                    style={inputStyle}
                  />
                </div>
              </div>

              {/* Total value */}
              {quantity && limitPrice && (
                <div className="text-xs text-gray-500">
                  Total value: <span className="text-gray-300 font-medium">
                    ₹{(Number(quantity) * Number(limitPrice)).toLocaleString()}
                  </span>
                </div>
              )}

              {/* Message */}
              {msg && (
                <div className="rounded-lg px-4 py-2 text-xs font-medium"
                  style={{
                    background: msgType === 'success' ? '#10b98115' : '#ef444415',
                    color: msgType === 'success' ? '#10b981' : '#ef4444',
                    border: `1px solid ${msgType === 'success' ? '#10b98130' : '#ef444430'}`,
                  }}>
                  {msg}
                </div>
              )}

              <button
                onClick={placeTrade}
                className="w-full rounded-lg py-2.5 text-sm font-medium text-white transition-colors"
                style={{ background: '#3b82f6' }}
                onMouseEnter={e => (e.currentTarget.style.background = '#2563eb')}
                onMouseLeave={e => (e.currentTarget.style.background = '#3b82f6')}>
                Place Trade
              </button>
            </div>
          </div>
        </div>

        {/* Current Positions */}
        <div className="rounded-xl border overflow-hidden" style={{ borderColor, background: '#1a1d2e' }}>
          <div className="flex items-center justify-between px-4 py-3" style={{ borderBottom: `1px solid ${borderColor}` }}>
            <h2 className="text-sm font-semibold text-gray-200">Active Positions</h2>
            <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded">{activePositions.length}</span>
          </div>
          {activePositions.length === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-gray-600">No active positions</div>
          ) : (
            <table className="w-full">
              <thead>
                <tr style={{ borderBottom: `1px solid ${borderColor}` }}>
                  <th className={thClass} style={{ textAlign: 'left' }}>ETF</th>
                  <th className={thClass} style={{ textAlign: 'right' }}>Tranches</th>
                  <th className={thClass} style={{ textAlign: 'right' }}>Units</th>
                  <th className={thClass} style={{ textAlign: 'right' }}>WAC</th>
                  <th className={thClass} style={{ textAlign: 'right' }}>Capital</th>
                </tr>
              </thead>
              <tbody>
                {activePositions.map(p => (
                  <tr key={p.id} style={{ borderBottom: `1px solid ${borderColor}` }}>
                    <td className={tdClass} style={{ fontWeight: 500, color: '#e2e8f0' }}>{p.etf_symbol}</td>
                    <td className={tdClass} style={{ textAlign: 'right' }}>{p.tranches_used}</td>
                    <td className={tdClass} style={{ textAlign: 'right' }}>{p.total_units}</td>
                    <td className={tdClass} style={{ textAlign: 'right' }}>
                      {p.weighted_avg_cost ? `₹${p.weighted_avg_cost.toFixed(2)}` : '-'}
                    </td>
                    <td className={tdClass} style={{ textAlign: 'right' }}>
                      ₹{p.total_capital_deployed.toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Recent Trades */}
      <div className="rounded-xl border overflow-hidden mt-6" style={{ borderColor, background: '#1a1d2e' }}>
        <div className="flex items-center justify-between px-4 py-3" style={{ borderBottom: `1px solid ${borderColor}` }}>
          <h2 className="text-sm font-semibold text-gray-200">Recent Trades</h2>
        </div>
        {recentTrades.length === 0 ? (
          <div className="px-4 py-8 text-center text-sm text-gray-600">No trades yet</div>
        ) : (
          <table className="w-full">
            <thead>
              <tr style={{ borderBottom: `1px solid ${borderColor}` }}>
                <th className={thClass} style={{ textAlign: 'left' }}>Symbol</th>
                <th className={thClass} style={{ textAlign: 'left' }}>Action</th>
                <th className={thClass} style={{ textAlign: 'right' }}>Qty</th>
                <th className={thClass} style={{ textAlign: 'right' }}>Price</th>
                <th className={thClass} style={{ textAlign: 'left' }}>Date</th>
              </tr>
            </thead>
            <tbody>
              {recentTrades.map(t => (
                <tr key={t.id} style={{ borderBottom: `1px solid ${borderColor}` }}>
                  <td className={tdClass} style={{ fontWeight: 500, color: '#e2e8f0' }}>{t.symbol}</td>
                  <td className={tdClass}>
                    <span className="px-2 py-0.5 rounded text-xs font-medium"
                      style={{
                        background: t.action.startsWith('exit') ? '#ef444415' : '#10b98115',
                        color: t.action.startsWith('exit') ? '#ef4444' : '#10b981',
                      }}>
                      {t.action.replace('_', ' ')}
                    </span>
                  </td>
                  <td className={tdClass} style={{ textAlign: 'right' }}>{t.quantity}</td>
                  <td className={tdClass} style={{ textAlign: 'right' }}>
                    {t.fill_price ? `₹${t.fill_price.toFixed(2)}` : '-'}
                  </td>
                  <td className={tdClass} style={{ color: '#64748b' }}>
                    {t.filled_at?.split('T')[0] || '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
