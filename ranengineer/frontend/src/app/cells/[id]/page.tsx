'use client'

import { use, useEffect, useState } from 'react'
import Link from 'next/link'
import { CellAnalysisReport, getCellAnalysis } from '../../../lib/api'

const severityClass = (status: string) => {
  const s = status.toLowerCase()
  if (s === 'healthy') return 'bg-teal-950 text-teal-300 border border-teal-800'
  if (s === 'warning') return 'bg-amber-950 text-amber-300 border border-amber-800'
  if (s === 'critical') return 'bg-red-950 text-red-300 border border-red-800'
  return 'bg-slate-800 text-slate-300'
}

export default function CellDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const cellId = decodeURIComponent(resolvedParams.id)

  const [analysis, setAnalysis] = useState<CellAnalysisReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadCell()
  }, [cellId])

  async function loadCell() {
    setLoading(true)
    setError('')
    try {
      const data = await getCellAnalysis(cellId)
      setAnalysis(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Cell not found.')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <main className="mx-auto max-w-7xl px-5 py-12 text-center text-slate-400">
        Loading cell diagnostics and telemetry for {cellId}…
      </main>
    )
  }

  if (error || !analysis) {
    return (
      <main className="mx-auto max-w-7xl px-5 py-12">
        <div className="rounded-lg border border-red-900 bg-red-950/60 p-4 text-sm text-red-200">
          <strong>Error: </strong>{error || 'Cell not found.'}
        </div>
        <Link href="/cells" className="mt-4 inline-block text-xs text-teal-400 hover:underline">
          ← Back to Cells
        </Link>
      </main>
    )
  }

  const kpis = analysis.kpis || {}
  const kpiStatuses = analysis.kpi_statuses || {}

  return (
    <main className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
      {/* Breadcrumb */}
      <div className="mb-6 flex items-center gap-2 text-xs text-slate-500 font-mono">
        <Link href="/cells" className="hover:text-slate-300">Cells</Link>
        <span>/</span>
        <span className="text-teal-400">{analysis.cell_id}</span>
      </div>

      {/* Header Card */}
      <div className="mb-8 rounded-2xl border border-slate-800 bg-slate-900 p-6 flex flex-col justify-between gap-6 md:flex-row md:items-center">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl font-bold font-mono tracking-tight text-teal-300">{analysis.cell_id}</h1>
            <span className={`inline-flex px-2.5 py-0.5 rounded text-xs font-bold tracking-wider ${severityClass(analysis.status)}`}>
              {analysis.status}
            </span>
            <span className="rounded bg-slate-800 px-2 py-0.5 font-mono text-xs text-slate-400">
              {analysis.technology || '4G LTE'}
            </span>
          </div>

          <p className="text-sm text-slate-400">
            Site ID: <strong className="font-mono text-slate-200">{analysis.site_id || 'N/A'}</strong>
            <span className="mx-2 text-slate-600">•</span>
            {analysis.summary}
          </p>
        </div>

        <div className="flex items-center gap-6">
          <div className="text-right">
            <p className="text-xs text-slate-400 font-mono">Cell Health Score</p>
            <p className="text-4xl font-bold font-mono text-teal-400">
              {analysis.health_score ?? '—'}
              <span className="text-sm font-normal text-slate-500">/100</span>
            </p>
          </div>

          <Link
            href={`/chat?question=Why%20is%20${encodeURIComponent(analysis.cell_id)}%20performing%20badly%3F`}
            className="rounded-lg bg-teal-400 px-4 py-2.5 text-xs font-bold text-slate-950 hover:bg-teal-300 shadow-md shadow-teal-500/10"
          >
            Investigate with Copilot
          </Link>
        </div>
      </div>

      {/* Grid: Measured KPIs & Probable Causes */}
      <div className="grid gap-6 lg:grid-cols-2 mb-8">
        {/* Measured KPIs Table / Cards */}
        <section className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <h2 className="font-semibold text-slate-200 mb-1">Measured KPI Telemetry</h2>
          <p className="text-xs text-slate-400 mb-4">Threshold status evaluated against telecom definitions</p>

          <div className="space-y-2.5">
            {Object.entries(kpis).map(([kpiName, value]) => {
              const status = kpiStatuses[kpiName] || 'UNKNOWN'
              return (
                <div key={kpiName} className="flex items-center justify-between rounded-lg bg-slate-950/70 p-3 border border-slate-800/80">
                  <div>
                    <span className="font-mono text-xs uppercase text-slate-300 font-semibold">{kpiName}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-sm font-bold text-slate-200">
                      {value !== null ? value : '—'}
                    </span>
                    <span className={`inline-flex px-2 py-0.5 rounded text-[10px] font-bold tracking-wider ${severityClass(status)}`}>
                      {status}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </section>

        {/* Probable Causes & Recommended Checks */}
        <div className="space-y-6">
          {/* Probable Causes */}
          <section className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <h2 className="font-semibold text-slate-200 mb-1">Probable Root Causes</h2>
            <p className="text-xs text-slate-400 mb-4">Rule-based engineering interpretations (Section 11 & 17)</p>

            {analysis.probable_causes.length === 0 ? (
              <p className="text-xs text-slate-500 italic">
                No active threshold combinations match specific degradation rules.
              </p>
            ) : (
              <div className="space-y-3">
                {analysis.probable_causes.map((cause, idx) => (
                  <div key={idx} className="rounded-lg border border-amber-900/50 bg-amber-950/20 p-3.5">
                    <p className="text-xs font-bold text-amber-300">
                      Probable Cause: {cause.probable_cause}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Recommended Engineering Checks */}
          <section className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <h2 className="font-semibold text-slate-200 mb-1">Recommended Engineering Checks</h2>
            <p className="text-xs text-slate-400 mb-4">Actionable diagnostic steps for field and optimization teams</p>

            {analysis.recommended_checks.length === 0 ? (
              <p className="text-xs text-slate-500">Perform routine radio parameter verification.</p>
            ) : (
              <ol className="space-y-2 list-decimal list-inside text-xs text-slate-300">
                {analysis.recommended_checks.map((check, idx) => (
                  <li key={idx} className="leading-relaxed pl-1">
                    <span className="text-slate-200">{check}</span>
                  </li>
                ))}
              </ol>
            )}

            <div className="mt-4 border-t border-slate-800/80 pt-3 text-[11px] text-slate-500">
              <strong>Limitations: </strong>{analysis.limitations}
            </div>
          </section>
        </div>
      </div>
    </main>
  )
}

