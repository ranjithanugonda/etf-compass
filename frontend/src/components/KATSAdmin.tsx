import { useEffect, useState } from 'react'
import { api } from '../api'
import type { StrategyParam, ETFAdmin } from '../types'

export default function KATSAdmin() {
  const [tab, setTab] = useState<'params' | 'etfs' | 'system' | 'jobs'>('params')
  const tabs = ['params', 'etfs', 'system', 'jobs'] as const

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-1 h-6 rounded-full bg-red-500" />
        <h1 className="text-xl font-semibold text-white">KATS Admin</h1>
      </div>

      <div className="flex gap-1 mb-6" style={{ background: '#1a1d2e', borderRadius: 8, padding: 2, display: 'inline-flex' }}>
        {tabs.map(t => (
          <button key={t}
            onClick={() => setTab(t)}
            className="px-4 py-1.5 text-xs font-medium rounded transition-all"
            style={{
              background: tab === t ? '#3b82f6' : 'transparent',
              color: tab === t ? '#fff' : '#94a3b8',
            }}>
            {t === 'params' ? 'Strategy Params' : t === 'etfs' ? 'ETF Manager' : t === 'system' ? 'System' : 'Jobs'}
          </button>
        ))}
      </div>

      {tab === 'params' && <ParamsEditor />}
      {tab === 'etfs' && <ETFManager />}
      {tab === 'system' && <SystemControls />}
      {tab === 'jobs' && <JobsPanel />}
    </div>
  )
}

function ParamsEditor() {
  const [params, setParams] = useState<StrategyParam[]>([])
  const [editing, setEditing] = useState<string | null>(null)
  const [editVal, setEditVal] = useState('')
  const [msg, setMsg] = useState('')

  useEffect(() => {
    fetch('/api/admin/strategy-params').then(r => r.json()).then(setParams).catch(() => {})
  }, [])

  const save = async (name: string) => {
    try {
      const val = isNaN(Number(editVal)) ? editVal : Number(editVal)
      await api.updateParam(name, val)
      setParams(prev => prev.map(p => p.param_name === name ? { ...p, param_value: val } : p))
      setEditing(null)
      setMsg(`Updated ${name}`)
      setTimeout(() => setMsg(''), 2000)
    } catch { setMsg('Save failed') }
  }

  const borderColor = '#2a2d3e'
  const thClass = 'p-3 text-xs font-medium text-gray-400 uppercase tracking-wider'
  const inputStyle = { background: '#141720', borderColor: '#2a2d3e', color: '#e2e8f0' }

  return (
    <div>
      {msg && (
        <div className="rounded-lg px-4 py-2 text-sm mb-4"
             style={{ background: '#10b98115', color: '#10b981', border: '1px solid #10b98130' }}>
          {msg}
        </div>
      )}
      <div className="rounded-xl border overflow-hidden" style={{ borderColor, background: '#1a1d2e' }}>
        <table className="w-full">
          <thead>
            <tr style={{ borderBottom: `1px solid ${borderColor}` }}>
              <th className={thClass} style={{ textAlign: 'left' }}>Param</th>
              <th className={thClass} style={{ textAlign: 'left' }}>Value</th>
              <th className={thClass} style={{ textAlign: 'left' }}>Description</th>
              <th className={thClass} style={{ textAlign: 'right' }}></th>
            </tr>
          </thead>
          <tbody>
            {params.map(p => (
              <tr key={p.param_name} style={{ borderBottom: `1px solid ${borderColor}` }}>
                <td className="p-3 text-xs font-mono" style={{ color: '#94a3b8' }}>{p.param_name}</td>
                {editing === p.param_name ? (
                  <>
                    <td className="p-3">
                      <input className="rounded-lg px-3 py-1.5 text-sm w-28 border"
                        style={inputStyle} value={editVal} autoFocus
                        onChange={e => setEditVal(e.target.value)} />
                    </td>
                    <td className="p-3 text-xs text-gray-500">{p.description}</td>
                    <td className="p-3" style={{ textAlign: 'right' }}>
                      <button className="text-emerald-400 text-xs mr-3 font-medium"
                        onClick={() => save(p.param_name)}>Save</button>
                      <button className="text-gray-500 text-xs"
                        onClick={() => setEditing(null)}>Cancel</button>
                    </td>
                  </>
                ) : (
                  <>
                    <td className="p-3 text-sm font-mono text-gray-200">
                      {typeof p.param_value === 'object'
                        ? JSON.stringify(p.param_value) : String(p.param_value)}
                    </td>
                    <td className="p-3 text-xs text-gray-500">{p.description}</td>
                    <td className="p-3" style={{ textAlign: 'right' }}>
                      <button className="text-blue-400 text-xs font-medium"
                        onClick={() => { setEditing(p.param_name); setEditVal(
                          typeof p.param_value === 'object'
                            ? JSON.stringify(p.param_value) : String(p.param_value)
                        ) }}>
                        Edit
                      </button>
                    </td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function ETFManager() {
  const [etfs, setEtfs] = useState<ETFAdmin[]>([])
  const load = () => {
    fetch('/api/admin/etfs').then(r => r.json()).then(setEtfs).catch(() => {})
  }
  useEffect(load, [])
  const toggle = async (symbol: string, active: boolean) => {
    try {
      await fetch(`/api/admin/etfs/${symbol}?active=${active}`, { method: 'PUT' })
      setEtfs(prev => prev.map(e => e.symbol === symbol ? { ...e, active } : e))
    } catch {}
  }
  const borderColor = '#2a2d3e'
  const thClass = 'p-3 text-xs font-medium text-gray-400 uppercase tracking-wider'

  return (
    <div className="rounded-xl border overflow-hidden" style={{ borderColor, background: '#1a1d2e' }}>
      <table className="w-full">
        <thead>
          <tr style={{ borderBottom: `1px solid ${borderColor}` }}>
            <th className={thClass} style={{ textAlign: 'left' }}>Symbol</th>
            <th className={thClass} style={{ textAlign: 'left' }}>Name</th>
            <th className={thClass} style={{ textAlign: 'left' }}>Category</th>
            <th className={thClass} style={{ textAlign: 'left' }}>Status</th>
          </tr>
        </thead>
        <tbody>
          {etfs.map(e => (
            <tr key={e.symbol} style={{ borderBottom: `1px solid ${borderColor}` }}>
              <td className="p-3 text-sm font-medium text-gray-200">{e.symbol}</td>
              <td className="p-3 text-xs text-gray-400">{e.name}</td>
              <td className="p-3 text-xs text-gray-500">{e.category}</td>
              <td className="p-3">
                <button onClick={() => toggle(e.symbol, !e.active)}
                  className="px-2.5 py-1 rounded text-xs font-medium border transition-colors"
                  style={{
                    background: e.active ? '#10b98115' : '#ef444415',
                    color: e.active ? '#10b981' : '#ef4444',
                    borderColor: e.active ? '#10b98130' : '#ef444430',
                  }}>
                  {e.active ? 'Active' : 'Inactive'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function SystemControls() {
  const [msg, setMsg] = useState('')
  const pause = async () => {
    try {
      await fetch('/api/admin/pause', { method: 'POST' })
      setMsg('System paused')
    } catch { setMsg('Failed') }
    setTimeout(() => setMsg(''), 2000)
  }
  const resume = async () => {
    try {
      await fetch('/api/admin/resume', { method: 'POST' })
      setMsg('System resumed')
    } catch { setMsg('Failed') }
    setTimeout(() => setMsg(''), 2000)
  }

  return (
    <div>
      <div className="rounded-xl border p-6" style={{ borderColor: '#2a2d3e', background: '#1a1d2e' }}>
        <p className="text-sm text-gray-400 mb-6">
          Pause stops all new signal generation. Resume restarts the automated system.
        </p>
        {msg && (
          <div className="rounded-lg px-4 py-2 text-sm mb-4"
               style={{ background: '#3b82f615', color: '#60a5fa', border: '1px solid #3b82f630' }}>
            {msg}
          </div>
        )}
        <div className="flex gap-3">
          <button onClick={pause}
            className="px-5 py-2 rounded-lg text-sm font-medium text-white
                       bg-red-600 hover:bg-red-700 transition-colors">
            Pause System
          </button>
          <button onClick={resume}
            className="px-5 py-2 rounded-lg text-sm font-medium text-white
                       bg-emerald-600 hover:bg-emerald-700 transition-colors">
            Resume System
          </button>
        </div>
      </div>
    </div>
  )
}

function JobsPanel() {
  const [msg, setMsg] = useState('')
  const [msgType, setMsgType] = useState<'success' | 'error'>('success')
  const [running, setRunning] = useState<string | null>(null)
  const [auditLog, setAuditLog] = useState<string[]>([])

  const loadLog = () => {
    fetch('/api/admin/audit-log?lines=20').then(r => r.json()).then(setAuditLog).catch(() => {})
  }
  useEffect(loadLog, [])

  const runJob = async (endpoint: string, label: string) => {
    setRunning(label)
    setMsg('')
    try {
      const res = await fetch(endpoint, { method: 'POST' })
      if (!res.ok) {
        const err = await res.json()
        setMsg(err.detail || 'Job failed')
        setMsgType('error')
      } else {
        const data = await res.json()
        setMsg(`${label} completed: ${JSON.stringify(data)}`)
        setMsgType('success')
        loadLog()
      }
    } catch {
      setMsg('Network error')
      setMsgType('error')
    }
    setRunning(null)
  }

  const btnClass = 'px-5 py-2.5 rounded-lg text-sm font-medium text-white transition-colors disabled:opacity-50'

  return (
    <div className="space-y-6">
      {/* Job Triggers */}
      <div className="rounded-xl border p-6" style={{ borderColor: '#2a2d3e', background: '#1a1d2e' }}>
        <h2 className="text-sm font-semibold text-gray-200 mb-4">Job Triggers</h2>
        <p className="text-xs text-gray-500 mb-4">
          Manually trigger system jobs. Backtest replays 2 years of history. EOD scan runs the strategy on latest data.
        </p>
        {msg && (
          <div className="rounded-lg px-4 py-2 text-xs font-medium mb-4 font-mono"
               style={{
                 background: msgType === 'success' ? '#10b98115' : '#ef444415',
                 color: msgType === 'success' ? '#10b981' : '#ef4444',
                 border: `1px solid ${msgType === 'success' ? '#10b98130' : '#ef444430'}`,
               }}>
            {msg}
          </div>
        )}
        <div className="flex flex-wrap gap-3">
          <button onClick={() => runJob('/api/admin/run-backtest', 'Run Backtest')}
            disabled={running !== null}
            className={btnClass} style={{ background: '#7c3aed' }}>
            {running === 'Run Backtest' ? 'Running...' : 'Run Backtest'}
          </button>
          <button onClick={() => runJob('/api/admin/run-eod-scan', 'Run EOD Scan')}
            disabled={running !== null}
            className={btnClass} style={{ background: '#3b82f6' }}>
            {running === 'Run EOD Scan' ? 'Running...' : 'Run EOD Scan'}
          </button>
          <button onClick={() => runJob('/api/admin/run-morning-execute', 'Run Morning Execute')}
            disabled={running !== null}
            className={btnClass} style={{ background: '#10b981' }}>
            {running === 'Run Morning Execute' ? 'Running...' : 'Run Morning Execute'}
          </button>
        </div>
      </div>

      {/* Audit Log */}
      <div className="rounded-xl border overflow-hidden" style={{ borderColor: '#2a2d3e', background: '#1a1d2e' }}>
        <div className="flex items-center justify-between px-4 py-3" style={{ borderBottom: '1px solid #2a2d3e' }}>
          <h2 className="text-sm font-semibold text-gray-200">Audit Log</h2>
          <button onClick={loadLog} className="text-xs text-blue-400 hover:text-blue-300">Refresh</button>
        </div>
        <div className="p-4">
          {auditLog.length === 0 ? (
            <p className="text-xs text-gray-600">No log entries yet.</p>
          ) : (
            <div className="space-y-1 max-h-80 overflow-y-auto">
              {auditLog.map((line, i) => (
                <div key={i} className="text-xs font-mono text-gray-400 py-0.5"
                  style={{ borderBottom: '1px solid #1e2130' }}>
                  {line}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
