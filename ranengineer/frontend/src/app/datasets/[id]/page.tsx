'use client'

import { use, useEffect, useState } from 'react'
import Link from 'next/link'
import { CellAnalysis, DatasetAnalysis, getDataset } from '../../../lib/api'

const severityClass = (status: string) => {
  const s = status.toLowerCase()
  if (s === 'healthy') return 'bg-teal-950 text-teal-300 border border-teal-800'
  if (s === 'warning') return 'bg-amber-950 text-amber-300 border border-amber-800'
  if (s === 'critical') return 'bg-red-950 text-red-300 border border-red-800'
  return 'bg-slate-800 text-slate-300'
}

export default function DatasetDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const datasetId = resolvedParams.id

  const [dataset, setDataset] = useState<DatasetAnalysis | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState<'worst' | 'anomalies' | 'all'>('worst')
  const [search, setSearch] = useState('')

  useEffect(() => {
    loadDataset()
  }, [datasetId])

  async function loadDataset() {
    setLoading(true)
    setError('')
    try {
      const data = await getDataset(datasetId)
      setDataset(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch dataset.')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <main className="mx-auto max-w-7xl px-5 py-12 text-center text-slate-400">
        Loading dataset telemetry…
      </main>
    )
  }

  if (error || !dataset) {
    return (
      <main className="mx-auto max-w-7xl px-5 py-12">
        <div className="rounded-lg border border-red-900 bg-red-950/60 p-4 text-sm text-red-200">
          <strong>Error: </strong>{error || 'Dataset not found.'}
        </div>
        <Link href="/datasets" className="mt-4 inline-block text-xs text-teal-400 hover:underline">
          ← Back to Datasets
        </Link>
      </main>
    )
  }

  const summary = dataset.summary
  const cells = dataset.cells || []

  // Filtered cells based on activeTab and search
  let displayCells: CellAnalysis[] = []
  if (activeTab === 'worst') {
    displayCells = cells.slice(0, 20)
  } else if (activeTab === 'anomalies') {
    displayCells = cells.filter(c => c.status === 'CRITICAL')
  } else {
    displayCells = cells
  }

  if (search.trim()) {
    const q = search.toLowerCase()
    displayCells = displayCells.filter(c => c.cell_id.toLowerCase().includes(q) || (c.site_id && c.site_id.toLowerCase().includes(q)))
  }

  return (
    <main className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
      {/* Breadcrumb & Header */}
      <div className="mb-6 flex items-center gap-2 text-xs text-slate-500 font-mono">
        <Link href="/datasets" className="hover:text-slate-300">Datasets</Link>
        <span>/</span>
        <span className="text-teal-400">{dataset.filename}</span>
      </div>

      <div className="mb-8 flex flex-col justify-between gap-4 border-b border-slate-800 pb-6 sm:flex-row sm:items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-100">{dataset.filename}</h1>
          <p className="mt-1 text-sm text-slate-400">
            Dataset ID: <span className="font-mono text-xs text-slate-300">{dataset.id}</span>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href={`/chat?dataset=${dataset.id}`}
            className="rounded-lg bg-teal-400 px-4 py-2 text-xs font-bold text-slate-950 hover:bg-teal-300 shadow-md shadow-teal-500/10"
          >
            Ask Copilot About Dataset
          </Link>
        </div>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5 mb-8">
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
          <p className="text-xs text-slate-400">Total Cells</p>
          <p className="mt-1 text-2xl font-bold text-slate-100">{summary.total_cells}</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
          <p className="text-xs text-teal-400">Healthy</p>
          <p className="mt-1 text-2xl font-bold text-teal-300">{summary.healthy_cells}</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
          <p className="text-xs text-amber-400">Warning</p>
          <p className="mt-1 text-2xl font-bold text-amber-300">{summary.warning_cells}</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
          <p className="text-xs text-red-400">Critical</p>
          <p className="mt-1 text-2xl font-bold text-red-300">{summary.critical_cells}</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
          <p className="text-xs text-slate-400">Avg Health Score</p>
          <p className="mt-1 text-2xl font-bold text-teal-400">{summary.average_health_score ?? '—'}/100</p>
        </div>
      </div>

      {/* Available KPIs metadata */}
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-4 mb-8 text-xs flex flex-wrap items-center justify-between gap-4">
        <div>
          <span className="text-slate-400 font-medium">Available KPIs: </span>
          <span className="font-mono text-teal-300">{dataset.available_kpis.join(', ') || 'None'}</span>
        </div>
        {dataset.unsupported_columns?.length > 0 && (
          <div>
            <span className="text-slate-400">Unsupported Columns: </span>
            <span className="font-mono text-slate-500">{dataset.unsupported_columns.join(', ')}</span>
          </div>
        )}
      </div>

      {/* Tabs & Search */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-4">
        <div className="flex gap-2 border-b border-slate-800 pb-2">
          <button
            onClick={() => setActiveTab('worst')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === 'worst' ? 'bg-slate-800 text-teal-300' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Worst 20 Cells
          </button>
          <button
            onClick={() => setActiveTab('anomalies')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === 'anomalies' ? 'bg-slate-800 text-teal-300' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Critical Anomalies ({summary.critical_cells})
          </button>
          <button
            onClick={() => setActiveTab('all')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === 'all' ? 'bg-slate-800 text-teal-300' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            All Cells ({summary.total_cells})
          </button>
        </div>

        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter by Cell ID or Site ID..."
          className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-teal-400"
        />
      </div>

      {/* Cell Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 uppercase tracking-wider text-slate-400 font-mono text-[11px]">
              <tr>
                <th>Cell ID</th>
                <th>Site ID</th>
                <th>Tech</th>
                <th>Health Score</th>
                <th>Status</th>
                <th>Issues</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {displayCells.map((cell) => (
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
              {displayCells.length === 0 && (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-500">
                    No cells matched current filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  )
}

