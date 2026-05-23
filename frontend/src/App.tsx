import { useState } from 'react'
import DecisionDashboard from './components/DecisionDashboard'
import BacktestDashboard from './components/BacktestDashboard'
import DiagnosticDashboard from './components/DiagnosticDashboard'
import EvidenceDashboard from './components/EvidenceDashboard'
import TradingDashboard from './components/TradingDashboard'
import KATSAdmin from './components/KATSAdmin'

const TABS = [
  { key: 'decision', label: 'Decision', comp: DecisionDashboard },
  { key: 'backtest', label: 'Backtest', comp: BacktestDashboard },
  { key: 'diagnostic', label: 'Diagnostic', comp: DiagnosticDashboard },
  { key: 'evidence', label: 'Evidence', comp: EvidenceDashboard },
  { key: 'trading', label: 'Trading', comp: TradingDashboard },
  { key: 'admin', label: 'Admin', comp: KATSAdmin },
] as const

export default function App() {
  const [tab, setTab] = useState('decision')
  const Comp = TABS.find(t => t.key === tab)?.comp ?? DecisionDashboard

  return (
    <div className="min-h-screen" style={{ background: '#0f1117' }}>
      <header style={{ background: '#0a0b10', borderBottom: '1px solid #1e2130' }}>
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
                  <rect width="28" height="28" rx="6" fill="#3b82f6"/>
                  <path d="M6 20L14 6l8 14H6z" fill="#0a0b10"/>
                  <path d="M10 16h8" stroke="#3b82f6" strokeWidth="2" strokeLinecap="round"/>
                </svg>
                <div>
                  <span className="text-lg font-bold tracking-tight text-white">
                    ETF Compass
                  </span>
                  <p className="text-xs text-gray-500 leading-tight"
                     style={{ maxWidth: 320 }}>
                    compounds capital by structure, not by emotion
                  </p>
                </div>
              </div>
            </div>
            <nav className="flex gap-0.5" style={{ background: '#1a1d2e', borderRadius: 8, padding: 2 }}>
              {TABS.map(t => (
                <button
                  key={t.key}
                  onClick={() => setTab(t.key)}
                  className="px-4 py-1.5 text-xs font-medium rounded transition-all"
                  style={{
                    background: tab === t.key ? '#3b82f6' : 'transparent',
                    color: tab === t.key ? '#fff' : '#94a3b8',
                  }}
                >
                  {t.label}
                </button>
              ))}
            </nav>
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-6 py-6">
        <Comp />
      </main>
    </div>
  )
}
