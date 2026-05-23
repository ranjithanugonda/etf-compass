import { useEffect, useState } from 'react'
import { api } from '../api'
import type { EvidenceData } from '../types'
import ETFDetailModal from './ETFDetailModal'

export default function EvidenceDashboard() {
  const [data, setData] = useState<EvidenceData | null>(null)
  const [err, setErr] = useState('')
  const [modalSymbol, setModalSymbol] = useState<string | null>(null)

  useEffect(() => {
    api.evidence().then(setData).catch(e => setErr(e.message))
  }, [])

  if (err) return <div className="text-red-400 p-4">Error: {err}</div>
  if (!data) return <div className="text-gray-400 p-4">Loading...</div>

  const borderColor = '#2a2d3e'
  const thClass = 'p-3 text-xs font-medium text-gray-400 uppercase tracking-wider'
  const tdClass = 'p-3 text-sm text-gray-300'

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-1 h-6 rounded-full bg-emerald-500" />
        <h1 className="text-xl font-semibold text-white">Evidence Dashboard</h1>
      </div>

      {/* Positions */}
      <Section title="Active Positions" count={data.positions.length}>
        {data.positions.length === 0 ? (
          <EmptyState message="No active positions" />
        ) : (
          <table className="w-full">
            <thead>
              <tr style={{ borderBottom: `1px solid ${borderColor}` }}>
                <th className={thClass} style={{ textAlign: 'left' }}>Symbol</th>
                <th className={thClass} style={{ textAlign: 'right' }}>Tranches</th>
                <th className={thClass} style={{ textAlign: 'right' }}>Capital</th>
                <th className={thClass} style={{ textAlign: 'right' }}>WAC</th>
              </tr>
            </thead>
            <tbody>
              {data.positions.map(p => (
                <tr key={p.symbol} style={{ borderBottom: `1px solid ${borderColor}`, cursor: 'pointer' }}
                    onClick={() => setModalSymbol(p.symbol)}
                    className="hover:bg-gray-800/50">
                  <td className={tdClass} style={{ fontWeight: 500 }}>
                    <span className="text-blue-400">{p.symbol}</span>
                  </td>
                  <td className={tdClass} style={{ textAlign: 'right' }}>{p.tranches_used}</td>
                  <td className={tdClass} style={{ textAlign: 'right' }}>₹{(p.capital_deployed || 0).toLocaleString()}</td>
                  <td className={tdClass} style={{ textAlign: 'right' }}>
                    {p.wac ? `₹${p.wac.toFixed(2)}` : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Section>

      {/* Trades */}
      <Section title="Recent Trades" count={data.recent_trades.length}>
        {data.recent_trades.length === 0 ? (
          <EmptyState message="No trades yet" />
        ) : (
          <table className="w-full">
            <thead>
              <tr style={{ borderBottom: `1px solid ${borderColor}` }}>
                <th className={thClass} style={{ textAlign: 'left' }}>Action</th>
                <th className={thClass} style={{ textAlign: 'right' }}>Qty</th>
                <th className={thClass} style={{ textAlign: 'right' }}>Fill</th>
                <th className={thClass} style={{ textAlign: 'left' }}>Date</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_trades.map(t => (
                <tr key={t.id} style={{ borderBottom: `1px solid ${borderColor}` }}>
                  <td className={tdClass}>
                    <ActionBadge action={t.action} />
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
      </Section>

      {/* Wiki */}
      <Section title="Wiki Pages" count={data.wiki_pages.length}>
        <div className="flex flex-wrap gap-2 p-3">
          {data.wiki_pages.map(sym => (
            <a key={sym} href={`/wiki/etfs/${sym}`} target="_blank"
               className="px-3 py-1 rounded-full text-xs font-medium
                          bg-blue-500/10 text-blue-400 border border-blue-500/20
                          hover:bg-blue-500/20 transition-colors">
              {sym}
            </a>
          ))}
        </div>
      </Section>

      {modalSymbol && (
        <ETFDetailModal
          symbol={modalSymbol}
          onClose={() => setModalSymbol(null)}
        />
      )}
    </div>
  )
}

function Section({ title, count, children }: {
  title: string; count: number; children: React.ReactNode
}) {
  return (
    <div className="mb-6 rounded-xl border overflow-hidden" style={{ borderColor: '#2a2d3e', background: '#1a1d2e' }}>
      <div className="flex items-center justify-between px-4 py-3" style={{ borderBottom: '1px solid #2a2d3e' }}>
        <h2 className="text-sm font-semibold text-gray-200">{title}</h2>
        <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded">{count}</span>
      </div>
      {children}
    </div>
  )
}

function ActionBadge({ action }: { action: string }) {
  const colors: Record<string, { bg: string; text: string; border: string }> = {
    entry: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20' },
    addon: { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/20' },
    exit_profit: { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/20' },
    exit_time: { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/20' },
  }
  const c = colors[action] || { bg: 'bg-gray-500/10', text: 'text-gray-400', border: 'border-gray-500/20' }
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium border ${c.bg} ${c.text} ${c.border}`}>
      {action}
    </span>
  )
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="px-4 py-8 text-center text-sm text-gray-600">{message}</div>
  )
}
