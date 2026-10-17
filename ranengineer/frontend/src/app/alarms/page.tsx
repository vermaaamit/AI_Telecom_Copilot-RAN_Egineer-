'use client'

import { useEffect, useState } from 'react'
import { listAlarms, AlarmItem } from '../../lib/api'

export default function AlarmsPage() {
  const [alarms, setAlarms] = useState<AlarmItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchAlarms() {
      try {
        setLoading(true)
        const data = await listAlarms()
        setAlarms(data)
      } catch (err: any) {
        setError(err.message || 'Failed to load alarms')
      } finally {
        setLoading(false)
      }
    }
    fetchAlarms()
  }, [])

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100">Active & Historical Alarms</h1>
          <p className="mt-1 text-sm text-slate-400">
            Telecom OSS/EMS persistent alarms integrated with PostgreSQL.
          </p>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-900/50 px-3 py-1.5 text-xs font-mono text-teal-400">
          Total: {alarms.length} Alarms
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
      ) : alarms.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-800 p-12 text-center text-sm text-slate-500">
          No alarms recorded in PostgreSQL datastore.
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/40">
          <table className="min-w-full divide-y divide-slate-800 text-left text-xs text-slate-300">
            <thead className="bg-slate-950/50 text-slate-400 font-medium">
              <tr>
                <th className="px-4 py-3">Alarm ID</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Severity</th>
                <th className="px-4 py-3">Target</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Description</th>
                <th className="px-4 py-3">Started At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {alarms.map((alarm) => (
                <tr key={alarm.alarm_id} className="hover:bg-slate-800/30 transition">
                  <td className="px-4 py-3 text-teal-300 font-semibold">{alarm.alarm_id}</td>
                  <td className="px-4 py-3">{alarm.alarm_type}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                        alarm.severity === 'CRITICAL'
                          ? 'bg-rose-950/80 text-rose-300 border border-rose-800'
                          : alarm.severity === 'MAJOR'
                          ? 'bg-amber-950/80 text-amber-300 border border-amber-800'
                          : 'bg-blue-950/80 text-blue-300 border border-blue-800'
                      }`}
                    >
                      {alarm.severity}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {alarm.cell_id || alarm.site_id || 'Global'}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-[10px] ${
                        alarm.status === 'ACTIVE'
                          ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {alarm.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 max-w-xs truncate font-sans text-slate-300">
                    {alarm.description}
                  </td>
                  <td className="px-4 py-3 text-slate-500 text-[11px]">
                    {new Date(alarm.started_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

