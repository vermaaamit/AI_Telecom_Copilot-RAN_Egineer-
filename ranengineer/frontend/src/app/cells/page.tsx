'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { CellAnalysis, listDatasets } from '../../lib/api'

const severityClass = (status: string) => {
  const s = status.toLowerCase()
  if (s === 'healthy') return 'bg-teal-950 text-teal-300 border border-teal-800'
  if (s === 'warning') return 'bg-amber-950 text-amber-300 border border-amber-800'
  if (s === 'critical') return 'bg-red-950 text-red-300 border border-red-800'
  return 'bg-slate-800 text-slate-300'
}

export default function CellsPage() {
  const [cells, setCells] = useState<CellAnalysis[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [techFilter, setTechFilter] = useState('')

  useEffect(() => {
    loadAllCells()
  }, [])

  async function loadAllCells() {
    setLoading(true)
    setError('')
    try {
      const datasets = await listDatasets()
      if (datasets.length > 0) {
        // Load cells from the latest dataset
        const full = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1'}/datasets/${datasets[0].id}`).then(r => r.json())
        setCells(full.cells || [])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load cells.')
    } finally {
      setLoading(false)
    }
  }

  const filteredCells = cells.filter((c) => {
    if (search.trim()) {
      const q = search.toLowerCase()
      const matchId = c.cell_id.toLowerCase().includes(q)
      const matchSite = c.site_id && c.site_id.toLowerCase().includes(q)
      if (!matchId && !matchSite) return false
    }
    if (statusFilter && c.status !== statusFilter) return false
    if (techFilter && c.technology !== techFilter) return false
    return true
  })

  return (
    <main className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
      {/* Header */}
      <div className="mb-8 flex flex-col justify-between gap-4 border-b border-slate-800 pb-6 sm:flex-row sm:items-end">
        <div>
          <span className="font-mono text-xs uppercase tracking-widest text-teal-400">Sector Inventory</span>
          <h1 className="text-3xl font-bold tracking-tight text-slate-100 mt-1">Cell Performance Explorer</h1>
          <p className="mt-1 text-sm text-slate-400">
            Browse and diagnose individual cell radio telemetry, throughput, and retainability metrics.
          </p>
        </div>

        <span className="font-mono text-xs text-slate-500">
          Showing {filteredCells.length} of {cells.length} cells
        </span>
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-red-900 bg-red-950/60 p-4 text-sm text-red-200">
          {error}
        </div>
      )}

      {/* Filter Controls */}
      <div className="mb-6 flex flex-wrap items-center gap-3">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by Cell ID (e.g. CELL102) or Site ID..."
          className="flex-1 min-w-[240px] rounded-lg border border-slate-800 bg-slate-900 px-3.5 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-teal-400"
        />

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-teal-400"
        >
          <option value="">All Statuses</option>
          <option value="CRITICAL">Critical Only</option>
          <option value="WARNING">Warning Only</option>
          <option value="HEALTHY">Healthy Only</option>
        </select>

        <select
          value={techFilter}
          onChange={(e) => setTechFilter(e.target.value)}
          className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-teal-400"
        >
          <option value="">All Technologies</option>
          <option value="4G">4G LTE</option>
          <option value="5G">5G NR</option>
        </select>
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
                <th>Active Breaches</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {loading && (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-400">
                    Loading cell inventory…
                  </td>
                </tr>
              )}
              {!loading && filteredCells.map((cell) => (
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
              {!loading && filteredCells.length === 0 && (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-500">
                    No cells found matching search criteria.
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

