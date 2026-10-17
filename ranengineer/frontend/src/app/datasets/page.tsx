'use client'

import { ChangeEvent, useEffect, useState } from 'react'
import Link from 'next/link'
import { DatasetAnalysis, listDatasets, uploadDataset } from '../../lib/api'

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<DatasetAnalysis[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchDatasets()
  }, [])

  async function fetchDatasets() {
    setLoading(true)
    setError('')
    try {
      const data = await listDatasets()
      setDatasets(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load datasets.')
    } finally {
      setLoading(false)
    }
  }

  async function handleUpload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    setError('')
    try {
      const created = await uploadDataset(file)
      setDatasets(prev => [created, ...prev])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <main className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
      <div className="mb-8 flex flex-col justify-between gap-4 border-b border-slate-800 pb-6 sm:flex-row sm:items-end">
        <div>
          <span className="font-mono text-xs uppercase tracking-widest text-teal-400">Dataset Repository</span>
          <h1 className="text-3xl font-bold tracking-tight text-slate-100 mt-1">Uploaded KPI Datasets</h1>
          <p className="mt-1 text-sm text-slate-400">
            Manage and inspect uploaded network telemetry exports across 4G LTE, 5G NR, and O-RAN sectors.
          </p>
        </div>

        <label className="inline-flex cursor-pointer items-center justify-center rounded-lg bg-teal-400 px-4 py-2 text-xs font-bold text-slate-950 transition hover:bg-teal-300">
          {uploading ? 'Analyzing CSV…' : '+ Upload New Dataset'}
          <input className="hidden" type="file" accept=".csv,text/csv" onChange={handleUpload} disabled={uploading} />
        </label>
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-red-900 bg-red-950/60 p-4 text-sm text-red-200">
          {error}
        </div>
      )}

      {loading && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-12 text-center text-slate-400">
          Loading datasets from database…
        </div>
      )}

      {!loading && datasets.length === 0 && (
        <div className="rounded-xl border border-dashed border-slate-800 bg-slate-900/40 p-16 text-center text-slate-400">
          No datasets found. Upload a KPI CSV file to begin.
        </div>
      )}

      {!loading && datasets.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {datasets.map((ds) => {
            const summary = ds.summary
            const dateStr = ds.created_at ? new Date(ds.created_at).toLocaleString() : 'Recent'
            return (
              <div key={ds.id} className="rounded-xl border border-slate-800 bg-slate-900 p-5 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="rounded bg-slate-800 px-2 py-0.5 font-mono text-[11px] text-teal-300">
                      {ds.technology || '4G/5G'}
                    </span>
                    <span className="text-[11px] text-slate-500 font-mono">{dateStr}</span>
                  </div>

                  <h3 className="font-semibold text-slate-200 truncate text-base" title={ds.filename}>
                    {ds.filename}
                  </h3>

                  <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                    <div className="rounded bg-slate-950/60 p-2 border border-slate-800/80">
                      <p className="text-slate-500 text-[10px]">Total Cells</p>
                      <p className="font-bold text-slate-200 mt-0.5">{ds.cell_count ?? ds.row_count}</p>
                    </div>
                    <div className="rounded bg-slate-950/60 p-2 border border-slate-800/80">
                      <p className="text-slate-500 text-[10px]">Avg Health Score</p>
                      <p className="font-bold text-teal-400 mt-0.5">
                        {summary?.average_health_score !== null ? `${summary?.average_health_score}/100` : '—'}
                      </p>
                    </div>
                  </div>

                  <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-800/60 pt-2">
                    <span>Critical: <strong className="text-red-400">{summary?.critical_cells ?? 0}</strong></span>
                    <span>Warning: <strong className="text-amber-400">{summary?.warning_cells ?? 0}</strong></span>
                    <span>Healthy: <strong className="text-teal-400">{summary?.healthy_cells ?? 0}</strong></span>
                  </div>
                </div>

                <div className="mt-5 flex items-center gap-2 border-t border-slate-800 pt-4">
                  <Link
                    href={`/datasets/${ds.id}`}
                    className="flex-1 rounded-lg bg-slate-800 py-2 text-center text-xs font-medium text-slate-200 hover:bg-slate-700"
                  >
                    View Details
                  </Link>
                  <Link
                    href={`/chat?dataset=${ds.id}`}
                    className="rounded-lg bg-teal-950 px-3 py-2 text-center text-xs font-medium text-teal-300 border border-teal-800 hover:bg-teal-900"
                  >
                    Chat
                  </Link>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </main>
  )
}

