import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { api } from '../services/api'
import type { AuditSession } from '../types'

export default function AuditPage() {
  const location = useLocation()
  const initial = (location.state as { sessionId?: string })?.sessionId
    ?? localStorage.getItem('lastSessionId')
    ?? ''

  const [sessionId, setSessionId] = useState(initial)
  const [data, setData] = useState<AuditSession | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const load = async (id: string) => {
    if (!id.trim()) return
    setLoading(true)
    setError(null)
    try {
      const result = await api.getAuditSession(id.trim())
      setData(result)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load audit')
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (initial) load(initial)
  }, [initial])

  return (
    <div className="space-y-8">
      <section>
        <h2 className="mb-2 text-2xl font-bold text-white">Agent Audit Console</h2>
        <p className="mb-4 text-slate-400">Structured agent actions and policy decisions — no hidden chain-of-thought.</p>
        <div className="flex gap-3">
          <input
            value={sessionId}
            onChange={(e) => setSessionId(e.target.value)}
            placeholder="Session UUID"
            className="flex-1 rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 text-white focus:border-brand-500 focus:outline-none"
          />
          <button
            onClick={() => load(sessionId)}
            disabled={loading}
            className="rounded-xl bg-brand-600 px-5 py-3 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
          >
            Load
          </button>
        </div>
      </section>

      {error && <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-red-300">{error}</div>}

      {data?.found && (
        <>
          <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
            <h3 className="mb-4 text-lg font-semibold text-white">Decision Flow</h3>
            <div className="space-y-4">
              {data.agent_actions.map((action) => (
                <div key={action.id} className="relative border-l-2 border-brand-500/50 pl-4">
                  <p className="font-medium text-brand-300 capitalize">{action.agent_type} Agent</p>
                  <p className="text-white">{action.action.replace(/_/g, ' ')}</p>
                  <p className="text-xs text-slate-500">{new Date(action.created_at).toLocaleString()}</p>
                </div>
              ))}
              {data.audit_logs.map((log) => (
                <div key={log.id} className="relative border-l-2 border-emerald-500/50 pl-4">
                  <p className="font-medium text-emerald-300">Policy Engine</p>
                  <p className="text-white">{log.action}</p>
                  <p className={`text-sm ${log.policy_result === 'APPROVED' ? 'text-emerald-400' : 'text-red-400'}`}>
                    {log.policy_result} — {log.reason}
                    {log.amount != null && ` (₹${Number(log.amount).toLocaleString('en-IN')})`}
                  </p>
                </div>
              ))}
            </div>
          </section>

          <section className="grid gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
              <h4 className="mb-3 font-semibold text-slate-300">Agent Actions</h4>
              <pre className="max-h-96 overflow-auto rounded-lg bg-slate-950 p-3 text-xs text-slate-400">
                {JSON.stringify(data.agent_actions, null, 2)}
              </pre>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
              <h4 className="mb-3 font-semibold text-slate-300">Audit Logs</h4>
              <pre className="max-h-96 overflow-auto rounded-lg bg-slate-950 p-3 text-xs text-slate-400">
                {JSON.stringify(data.audit_logs, null, 2)}
              </pre>
            </div>
          </section>
        </>
      )}
    </div>
  )
}
