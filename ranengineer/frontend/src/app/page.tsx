'use client'

import { ChangeEvent, useEffect, useState } from 'react'
import Link from 'next/link'
import {
  DatasetAnalysis,
  ShiftHandoverReport,
  getShiftHandoverExportUrl,
  getShiftHandoverReport,
  listDatasets,
  uploadDataset,
} from '../lib/api'

const severityClass = (status: string) => {
  const s = status.toLowerCase()
  if (s === 'healthy') return 'bg-teal-950 text-teal-300 border border-teal-800'
  if (s === 'warning') return 'bg-amber-950 text-amber-300 border border-amber-800'
  if (s === 'critical') return 'bg-red-950 text-red-300 border border-red-800'
  return 'bg-slate-800 text-slate-300'
}

export default function DashboardPage() {
  const [datasets, setDatasets] = useState<DatasetAnalysis[]>([])
  const [currentDataset, setCurrentDataset] = useState<DatasetAnalysis | null>(null)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [handoverReport, setHandoverReport] = useState<ShiftHandoverReport | null>(null)
  const [loadingReport, setLoadingReport] = useState(false)
  const [showReportModal, setShowReportModal] = useState(false)

  async function handleLoadHandoverReport() {
    setLoadingReport(true)
    setShowReportModal(true)
    try {
      const rep = await getShiftHandoverReport(currentDataset?.id)
      setHandoverReport(rep)
    } catch (err: any) {
      setError(err?.message || 'Failed to generate shift handover report.')
    } finally {
      setLoadingReport(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    setError('')
    try {
      const list = await listDatasets()
      setDatasets(list)
      if (list.length > 0) {
        // Fetch full dataset details for first one
        const full = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1'}/datasets/${list[0].id}`).then(r => r.json())
        setCurrentDataset(full)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect to API.')
    } finally {
      setLoading(false)
    }
  }

  async function handleFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return
    setUploading(true)
    setError('')
    try {
      const uploaded = await uploadDataset(file)
      setCurrentDataset(uploaded)
      setDatasets(prev => [uploaded, ...prev])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed.')
    } finally {
      setUploading(false)
    }
  }

  const summary = currentDataset?.summary
  const total = summary?.total_cells || 1
  const healthyPct = Math.round(((summary?.healthy_cells || 0) / total) * 100)
  const warningPct = Math.round(((summary?.warning_cells || 0) / total) * 100)
  const criticalPct = Math.round(((summary?.critical_cells || 0) / total) * 100)

  // Calculate major KPI problems breakdown across cells
  const cells = currentDataset?.cells || []
  const kpiIssues: Record<string, number> = {}
  cells.forEach(c => {
    c.issues.forEach(iss => {
      const kpiName = iss.replace(/^(CRITICAL|WARNING)_/, '')
      kpiIssues[kpiName] = (kpiIssues[kpiName] || 0) + 1
    })
  })
  const sortedKpiIssues = Object.entries(kpiIssues)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)

  return (
    <main className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
      {/* Top Banner & Dataset Selector */}
      <div className="mb-8 flex flex-col justify-between gap-4 border-b border-slate-800 pb-6 sm:flex-row sm:items-end">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="font-mono text-xs uppercase tracking-widest text-teal-400">Network Overview</span>
            {currentDataset && (
              <span className="rounded bg-slate-800 px-2 py-0.5 font-mono text-[11px] text-slate-300">
                {currentDataset.technology || '4G/5G'}
              </span>
            )}
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-100">RAN Engineering Dashboard</h1>
          <p className="mt-1 text-sm text-slate-400">
            Deterministic radio access network performance telemetry, anomaly diagnostics, and cell health scores.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {datasets.length > 1 && (
            <select
              value={currentDataset?.id}
              onChange={async (e) => {
                setLoading(true)
                const full = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1'}/datasets/${e.target.value}`).then(r => r.json())
                setCurrentDataset(full)
                setLoading(false)
              }}
              className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-teal-400"
            >
              {datasets.map(d => (
                <option key={d.id} value={d.id}>{d.filename} ({d.cell_count} cells)</option>
              ))}
            </select>
          )}

          <button
            onClick={handleLoadHandoverReport}
            className="inline-flex items-center gap-1.5 rounded-lg border border-cyan-500/40 bg-cyan-950/40 px-3.5 py-2 text-xs font-semibold text-cyan-300 hover:bg-cyan-900/40 transition shadow-sm"
          >
            📋 Shift Handover
          </button>

          <label className="inline-flex cursor-pointer items-center justify-center rounded-lg bg-teal-400 px-4 py-2 text-xs font-bold text-slate-950 transition hover:bg-teal-300 shadow-md shadow-teal-500/10">
            {uploading ? 'Analyzing CSV…' : 'Upload KPI CSV'}
            <input className="hidden" type="file" accept=".csv,text/csv" onChange={handleFile} disabled={uploading} />
          </label>
        </div>
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-red-900 bg-red-950/60 p-4 text-sm text-red-200">
          <strong>Error: </strong>{error}
        </div>
      )}

      {loading && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-12 text-center text-slate-400">
          Loading network telemetry and KPI scoring data…
        </div>
      )}

      {!loading && !currentDataset && (
        <div className="rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 p-16 text-center">
          <h3 className="text-lg font-semibold text-slate-200">No KPI datasets analyzed yet</h3>
          <p className="mx-auto mt-2 max-w-md text-sm text-slate-400">
            Upload your first telecom KPI CSV export to calculate deterministic cell health scores and detect underperforming cells.
          </p>
          <label className="mt-6 inline-flex cursor-pointer items-center rounded-lg bg-teal-400 px-5 py-2.5 text-xs font-bold text-slate-950 hover:bg-teal-300">
            Upload KPI CSV
            <input className="hidden" type="file" accept=".csv,text/csv" onChange={handleFile} />
          </label>
        </div>
      )}

      {!loading && currentDataset && summary && (
        <>
          {/* Section 1: KPI Stat Cards */}
          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            <article className="rounded-xl border border-slate-800 bg-slate-900 p-4">
              <p className="text-xs font-medium text-slate-400">Total Analyzed Cells</p>
              <p className="mt-2 text-3xl font-bold text-slate-100">{summary.total_cells}</p>
              <p className="mt-1 text-[11px] text-slate-500 font-mono">{currentDataset.filename}</p>
            </article>

            <article className="rounded-xl border border-slate-800 bg-slate-900 p-4">
              <p className="text-xs font-medium text-teal-400">Healthy Cells</p>
              <p className="mt-2 text-3xl font-bold text-teal-300">{summary.healthy_cells}</p>
              <p className="mt-1 text-[11px] text-teal-500 font-mono">{healthyPct}% of total</p>
            </article>

            <article className="rounded-xl border border-slate-800 bg-slate-900 p-4">
              <p className="text-xs font-medium text-amber-400">Warning Cells</p>
              <p className="mt-2 text-3xl font-bold text-amber-300">{summary.warning_cells}</p>
              <p className="mt-1 text-[11px] text-amber-500 font-mono">{warningPct}% of total</p>
            </article>

            <article className="rounded-xl border border-slate-800 bg-slate-900 p-4">
              <p className="text-xs font-medium text-red-400">Critical Cells</p>
              <p className="mt-2 text-3xl font-bold text-red-300">{summary.critical_cells}</p>
              <p className="mt-1 text-[11px] text-red-500 font-mono">{criticalPct}% of total</p>
            </article>

            <article className="rounded-xl border border-slate-800 bg-slate-900 p-4">
              <p className="text-xs font-medium text-slate-400">Network Health Score</p>
              <p className="mt-2 text-3xl font-bold text-teal-400">
                {summary.average_health_score !== null ? `${summary.average_health_score}` : '—'}
                <span className="text-xs font-normal text-slate-500"> /100</span>
              </p>
              <p className="mt-1 text-[11px] text-slate-500 font-mono">Weighted score</p>
            </article>
          </section>

          {/* Section 2: Distribution Bar Chart & Major KPI Problems */}
          <section className="mt-6 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
            {/* Visual Health Distribution Bar */}
            <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-sm text-slate-200">Network Health Distribution</h3>
                <span className="text-xs text-slate-400 font-mono">{summary.total_cells} Cells</span>
              </div>

              {/* Progress bar */}
              <div className="h-6 w-full rounded-lg bg-slate-950 overflow-hidden flex border border-slate-800">
                <div style={{ width: `${healthyPct}%` }} className="bg-teal-500 h-full transition-all" title={`Healthy: ${healthyPct}%`} />
                <div style={{ width: `${warningPct}%` }} className="bg-amber-500 h-full transition-all" title={`Warning: ${warningPct}%`} />
                <div style={{ width: `${criticalPct}%` }} className="bg-red-500 h-full transition-all" title={`Critical: ${criticalPct}%`} />
              </div>

              <div className="mt-4 flex flex-wrap items-center justify-between gap-4 text-xs">
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded bg-teal-500"></span>
                  <span className="text-slate-300">Healthy ({healthyPct}%)</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded bg-amber-500"></span>
                  <span className="text-slate-300">Warning ({warningPct}%)</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded bg-red-500"></span>
                  <span className="text-slate-300">Critical ({criticalPct}%)</span>
                </div>
              </div>

              <div className="mt-6 border-t border-slate-800/80 pt-4 flex items-center justify-between text-xs">
                <span className="text-slate-400">Available KPIs:</span>
                <span className="font-mono text-teal-300 truncate max-w-md">{currentDataset.available_kpis.join(', ')}</span>
              </div>
            </div>

            {/* Major KPI Problems */}
            <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
              <h3 className="font-semibold text-sm text-slate-200 mb-3">Major KPI Degradations</h3>
              <p className="text-xs text-slate-400 mb-4">Most frequent threshold breaches in this dataset</p>

              {sortedKpiIssues.length === 0 ? (
                <p className="text-xs text-slate-500">No significant KPI degradations detected.</p>
              ) : (
                <div className="space-y-3">
                  {sortedKpiIssues.map(([kpi, count]) => {
                    const pct = Math.round((count / summary.total_cells) * 100)
                    return (
                      <div key={kpi}>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="font-mono uppercase text-slate-300">{kpi}</span>
                          <span className="text-slate-400">{count} cells ({pct}%)</span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-slate-950 overflow-hidden">
                          <div style={{ width: `${Math.min(pct, 100)}%` }} className="h-full bg-red-400" />
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </section>

          {/* Section 3: Worst Underperforming Cells Table */}
          <section className="mt-6 rounded-xl border border-slate-800 bg-slate-900">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 px-5 py-4">
              <div>
                <h3 className="font-semibold text-slate-200">Worst Underperforming Cells</h3>
                <p className="text-xs text-slate-400">Ranked deterministically by cell health score</p>
              </div>
              <div className="flex items-center gap-3">
                <Link
                  href={`/chat?dataset=${currentDataset.id}`}
                  className="rounded-lg bg-teal-950 px-3 py-1.5 text-xs font-medium text-teal-300 border border-teal-800 hover:bg-teal-900"
                >
                  Ask Copilot
                </Link>
                <Link
                  href={`/cells?dataset=${currentDataset.id}`}
                  className="rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700"
                >
                  View All Cells →
                </Link>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/60 uppercase tracking-wider text-slate-400 font-mono text-[11px]">
                  <tr>
                    <th>Cell ID</th>
                    <th>Site ID</th>
                    <th>Tech</th>
                    <th>Health Score</th>
                    <th>Status</th>
                    <th>Breached Issues</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {cells.slice(0, 10).map((cell) => (
                    <tr key={cell.cell_id} className="hover:bg-slate-800/40 transition">
                      <td className="font-mono font-medium text-teal-300">
                        <Link href={`/cells/${encodeURIComponent(cell.cell_id)}`} className="hover:underline">
                          {cell.cell_id}
                        </Link>
                      </td>
                      <td className="font-mono text-slate-300">{cell.site_id || '—'}</td>
                      <td>
                        <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] font-mono text-slate-400">
                          {cell.technology || '4G'}
                        </span>
                      </td>
                      <td className="font-mono font-bold text-slate-200">{cell.health_score ?? '—'}/100</td>
                      <td>
                        <span className={`inline-flex px-2 py-0.5 rounded text-[10px] font-bold tracking-wider ${severityClass(cell.status)}`}>
                          {cell.status}
                        </span>
                      </td>
                      <td className="max-w-[320px] truncate text-slate-400">
                        {cell.issues.length ? cell.issues.join(', ') : 'None'}
                      </td>
                      <td>
                        <Link
                          href={`/cells/${encodeURIComponent(cell.cell_id)}`}
                          className="text-teal-400 hover:text-teal-300 font-medium"
                        >
                          Diagnose →
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
      {/* Shift Handover Briefing Modal */}
      {showReportModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
          <div className="max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-bold text-slate-100">
                    {handoverReport?.shift_title || 'NOC Operational Shift Handover'}
                  </h2>
                  {handoverReport && (
                    <span
                      className={`rounded px-2.5 py-0.5 text-xs font-mono font-bold ${
                        handoverReport.system_status === 'HEALTHY'
                          ? 'bg-teal-950 text-teal-300 border border-teal-700'
                          : handoverReport.system_status === 'DEGRADED'
                          ? 'bg-amber-950 text-amber-300 border border-amber-700'
                          : 'bg-rose-950 text-rose-300 border border-rose-700'
                      }`}
                    >
                      STATUS: {handoverReport.system_status}
                    </span>
                  )}
                </div>
                <p className="mt-1 text-xs text-slate-400 font-mono">
                  Report ID: {handoverReport?.report_id || 'Generating...'} | Prepared by:{' '}
                  {handoverReport?.prepared_by}
                </p>
              </div>

              <button
                onClick={() => setShowReportModal(false)}
                className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              >
                ✕
              </button>
            </div>

            {loadingReport ? (
              <div className="py-16 text-center text-slate-400 text-sm">
                Compiling multi-source telemetry, alarm correlations, and predictive warnings...
              </div>
            ) : handoverReport ? (
              <div className="mt-6 space-y-6 text-xs">
                {/* Executive Summary */}
                <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 leading-relaxed text-slate-300">
                  <h3 className="font-semibold text-slate-200 mb-1 text-sm">Executive Summary</h3>
                  <p>{handoverReport.executive_summary}</p>
                </div>

                {/* Key Metrics Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-center">
                    <span className="text-[10px] text-slate-500 uppercase font-mono">Monitored Cells</span>
                    <p className="text-lg font-bold text-slate-200 mt-1">
                      {handoverReport.total_cells_monitored}
                    </p>
                  </div>
                  <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-center">
                    <span className="text-[10px] text-slate-500 uppercase font-mono">Degraded Sectors</span>
                    <p className="text-lg font-bold text-rose-400 mt-1">
                      {handoverReport.degraded_cell_count}
                    </p>
                  </div>
                  <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-center">
                    <span className="text-[10px] text-slate-500 uppercase font-mono">Active Alarms</span>
                    <p className="text-lg font-bold text-amber-400 mt-1">
                      {handoverReport.active_alarms.length}
                    </p>
                  </div>
                  <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-center">
                    <span className="text-[10px] text-slate-500 uppercase font-mono">Open Incidents</span>
                    <p className="text-lg font-bold text-cyan-400 mt-1">
                      {handoverReport.open_incidents.length}
                    </p>
                  </div>
                </div>

                {/* Handover Action Checklist */}
                <div>
                  <h3 className="font-semibold text-slate-200 mb-2 text-sm">
                    Immediate Handover Action Items (Oncoming Shift)
                  </h3>
                  <div className="space-y-2">
                    {handoverReport.handover_action_items.map((item, idx) => (
                      <div
                        key={idx}
                        className="flex items-start gap-2.5 rounded-lg border border-slate-800 bg-slate-950/40 p-2.5"
                      >
                        <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-slate-800 font-mono text-[11px] text-cyan-400">
                          {idx + 1}
                        </span>
                        <span className="text-slate-300 leading-normal">{item}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Critical Cells List */}
                {handoverReport.critical_cells.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-slate-200 mb-2 text-sm">
                      Critical Cells Requiring Intervention ({handoverReport.critical_cells.length})
                    </h3>
                    <div className="overflow-x-auto rounded-lg border border-slate-800">
                      <table className="w-full text-left">
                        <thead className="bg-slate-950 text-slate-400 text-[11px]">
                          <tr>
                            <th className="p-2">Cell ID</th>
                            <th className="p-2">Site</th>
                            <th className="p-2">Score</th>
                            <th className="p-2">Status</th>
                            <th className="p-2">Primary Probable Cause</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800 bg-slate-900/40">
                          {handoverReport.critical_cells.slice(0, 5).map((c) => (
                            <tr key={c.cell_id}>
                              <td className="p-2 font-mono text-cyan-300">{c.cell_id}</td>
                              <td className="p-2 text-slate-400">{c.site_id || '—'}</td>
                              <td className="p-2 font-mono font-bold text-rose-400">
                                {c.health_score.toFixed(1)}/100
                              </td>
                              <td className="p-2">
                                <span className="rounded bg-rose-950 px-1.5 py-0.5 text-[10px] text-rose-300 border border-rose-800">
                                  {c.status}
                                </span>
                              </td>
                              <td className="p-2 text-slate-300">
                                {c.probable_causes[0] || c.top_issue || 'General Degradation'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Modal Footer Actions */}
                <div className="flex items-center justify-between border-t border-slate-800 pt-4">
                  <a
                    href={getShiftHandoverExportUrl(currentDataset?.id)}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 rounded-lg bg-cyan-500 px-4 py-2 font-semibold text-slate-950 hover:bg-cyan-400 transition"
                  >
                    ⬇ Export Shift Handover (Markdown)
                  </a>
                  <button
                    onClick={() => setShowReportModal(false)}
                    className="rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-slate-300 hover:bg-slate-700 transition"
                  >
                    Close
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </main>
  )
}
