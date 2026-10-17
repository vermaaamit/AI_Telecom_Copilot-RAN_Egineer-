'use client'

import { useEffect, useState } from 'react'
import { listIncidents, resolveIncident, IncidentItem } from '../../lib/api'

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<IncidentItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [resolvingId, setResolvingId] = useState<string | null>(null)
  const [resolutionText, setResolutionText] = useState('')

  async function loadIncidents() {
    try {
      setLoading(true)
      const data = await listIncidents()
      setIncidents(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load incidents')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadIncidents()
  }, [])

  async function handleResolve(incidentId: string) {
    if (!resolutionText.trim()) return
    try {
      await resolveIncident(incidentId, resolutionText)
      setResolvingId(null)
      setResolutionText('')
      await loadIncidents()
    } catch (err: any) {
      alert(`Resolution failed: ${err.message}`)
    }
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100">Network Incidents</h1>
          <p className="mt-1 text-sm text-slate-400">
            Telecom engineer ticket tracking, correlated root cause, and audit resolution.
          </p>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-900/50 px-3 py-1.5 text-xs font-mono text-teal-400">
          {incidents.filter((i) => i.status === 'OPEN').length} Open / {incidents.length} Total
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center p-12">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-teal-500 border-t-transparent" />
        </div>
      ) : error ? (
        <div className="rounded-lg border border-rose-900/50 bg-rose-950/20 p-4 text-sm text-rose-300">
          {error}
        </div>
      ) : incidents.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-800 p-12 text-center text-sm text-slate-500">
          No incidents registered.
        </div>
      ) : (
        <div className="space-y-4">
          {incidents.map((incident) => (
            <div
              key={incident.id}
              className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 transition hover:border-slate-700"
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-sm font-semibold text-teal-300">{incident.id}</span>
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                        incident.severity === 'CRITICAL'
                          ? 'bg-rose-950/80 text-rose-300 border border-rose-800'
                          : 'bg-amber-950/80 text-amber-300 border border-amber-800'
                      }`}
                    >
                      {incident.severity}
                    </span>
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-[10px] ${
                        incident.status === 'OPEN'
                          ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {incident.status}
                    </span>
                  </div>
                  <h3 className="mt-2 text-base font-medium text-slate-100">{incident.title}</h3>
                  <p className="mt-1 text-sm text-slate-400">{incident.description}</p>
                </div>
                <div className="text-right text-xs text-slate-500 font-mono">
                  {new Date(incident.created_at).toLocaleString()}
                </div>
              </div>

              {incident.affected_cells.length > 0 && (
                <div className="mt-3 flex items-center gap-2">
                  <span className="text-xs text-slate-500">Affected Cells:</span>
                  <div className="flex flex-wrap gap-1.5 font-mono text-[11px]">
                    {incident.affected_cells.map((cell) => (
                      <span key={cell} className="rounded bg-slate-800/80 px-2 py-0.5 text-slate-300">
                        {cell}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {incident.resolution && (
                <div className="mt-4 rounded-lg border border-emerald-900/40 bg-emerald-950/20 p-3 text-xs text-emerald-300">
                  <span className="font-bold">Resolution: </span>
                  {incident.resolution}
                </div>
              )}

              {incident.status === 'OPEN' && (
                <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between">
                  {resolvingId === incident.id ? (
                    <div className="flex w-full items-center gap-2">
                      <input
                        type="text"
                        placeholder="Resolution summary (e.g. antenna tilt adjusted, RRU rebooted)..."
                        value={resolutionText}
                        onChange={(e) => setResolutionText(e.target.value)}
                        className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-slate-200 outline-none focus:border-teal-500"
                      />
                      <button
                        onClick={() => handleResolve(incident.id)}
                        className="rounded-lg bg-teal-500 px-3 py-1.5 text-xs font-semibold text-slate-950 hover:bg-teal-400 transition"
                      >
                        Submit
                      </button>
                      <button
                        onClick={() => setResolvingId(null)}
                        className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => {
                        setResolvingId(incident.id)
                        setResolutionText('')
                      }}
                      className="rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-1 text-xs text-slate-300 hover:bg-slate-800 hover:text-slate-100 transition"
                    >
                      Resolve Incident
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

