'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import {
  CellAnalysis,
  listAnomalies,
  getPredictiveAnomalies,
  PredictiveAnomalyItem,
} from '../../lib/api'

export default function AnomaliesPage() {
  const [tab, setTab] = useState<'critical' | 'predictive'>('critical')
  const [anomalies, setAnomalies] = useState<CellAnalysis[]>([])
  const [predictiveItems, setPredictiveItems] = useState<PredictiveAnomalyItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    setError('')
    try {
      const [anomRes, predRes] = await Promise.all([
        listAnomalies(100),
        getPredictiveAnomalies().catch(() => ({ items: [] })),
      ])
      setAnomalies(anomRes.items || [])
      setPredictiveItems(predRes.items || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch network anomalies.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
      <div className="mb-8 flex flex-col justify-between gap-4 border-b border-slate-800 pb-6 sm:flex-row sm:items-end">
        <div>
          <span className="font-mono text-xs uppercase tracking-widest text-red-400">Network Intelligence</span>
          <h1 className="text-3xl font-bold tracking-tight text-slate-100 mt-1">Anomaly & Predictive Detection</h1>
          <p className="mt-1 text-sm text-slate-400">
            Real-time critical threshold breaches alongside predictive velocity degradation warnings.
          </p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setTab('critical')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition ${
              tab === 'critical'
                ? 'bg-rose-950/80 text-rose-300 border border-rose-800'
                : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
            }`}
          >
            Critical Anomalies ({anomalies.length})
          </button>
          <button
            onClick={() => setTab('predictive')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition ${
              tab === 'predictive'
                ? 'bg-amber-950/80 text-amber-300 border border-amber-800'
                : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
            }`}
          >
            Predictive Early-Warnings ({predictiveItems.length})
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-red-900 bg-red-950/60 p-4 text-sm text-red-200">
          {error}
        </div>
      )}

      {loading && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-12 text-center text-slate-400">
          Scanning for critical & predictive anomalies…
        </div>
      )}

      {!loading && tab === 'critical' && (
        <>
          {anomalies.length === 0 ? (
            <div className="rounded-xl border border-dashed border-teal-800 bg-teal-950/20 p-16 text-center text-teal-300">
              No critical anomalies detected in analyzed datasets. All monitored cells meet operational thresholds.
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {anomalies.map((cell) => (
                <div
                  key={cell.cell_id}
                  className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 transition hover:border-slate-700"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="font-mono text-xs font-bold text-teal-400">{cell.cell_id}</span>
                      <p className="text-xs text-slate-400">{cell.site_id || 'Unknown Site'}</p>
                    </div>
                    <span className="rounded bg-rose-950/80 px-2 py-0.5 text-[10px] font-bold text-rose-300 border border-rose-800">
                      Score: {cell.health_score ?? 'N/A'}/100
                    </span>
                  </div>

                  <div className="mt-3 space-y-1">
                    {cell.issues.slice(0, 3).map((issue, idx) => (
                      <div key={idx} className="text-xs text-rose-400 flex items-center gap-1.5">
                        <span className="h-1.5 w-1.5 rounded-full bg-rose-500" />
                        <span>{issue}</span>
                      </div>
                    ))}
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-800/60 flex justify-end">
                    <Link
                      href={`/cells/${cell.cell_id}`}
                      className="text-xs text-teal-400 hover:text-teal-300 font-medium"
                    >
                      View Cell RCA &rarr;
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {!loading && tab === 'predictive' && (
        <>
          {predictiveItems.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-800 p-16 text-center text-slate-500">
              No predictive anomalies detected. Telemetry velocities across historical intervals remain within safe bands.
            </div>
          ) : (
            <div className="space-y-4">
              {predictiveItems.map((item, idx) => (
                <div
                  key={idx}
                  className="rounded-xl border border-amber-900/40 bg-slate-900/50 p-5 transition hover:border-amber-800/60"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-sm font-semibold text-teal-300">{item.cell_id}</span>
                        <span className="rounded bg-amber-950/80 px-2 py-0.5 text-[10px] font-bold text-amber-300 border border-amber-800">
                          {item.risk_level}
                        </span>
                        <span className="text-xs font-mono text-slate-400">KPI: {item.kpi_name}</span>
                      </div>
                      <p className="mt-2 text-xs text-slate-300">{item.summary}</p>
                    </div>
                    <div className="text-right font-mono text-xs">
                      <div className="text-slate-400">Current: {item.current_value}</div>
                      <div className="text-rose-400 font-bold">Projected: {item.projected_value}</div>
                    </div>
                  </div>

                  <div className="mt-3 rounded-lg border border-teal-900/40 bg-teal-950/20 p-3 text-xs text-teal-300">
                    <span className="font-bold">Recommended Proactive Action: </span>
                    {item.recommended_action}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </main>
  )
}
