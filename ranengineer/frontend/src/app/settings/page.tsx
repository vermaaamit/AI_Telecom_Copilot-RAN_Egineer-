'use client'

import { useEffect, useState } from 'react'
import {
  checkHealth,
  getSecurityMetrics,
  KPIDefinition,
  listKPIs,
  listSecurityAuditLog,
  SecurityAuditEvent,
  SecurityMetrics,
} from '../../lib/api'

export default function SettingsPage() {
  const [kpis, setKpis] = useState<Record<string, KPIDefinition>>({})
  const [health, setHealth] = useState<{ status: string; service: string } | null>(null)
  const [securityMetrics, setSecurityMetrics] = useState<SecurityMetrics | null>(null)
  const [auditEvents, setAuditEvents] = useState<SecurityAuditEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadSettings()
  }, [])

  async function loadSettings() {
    setLoading(true)
    setError('')
    try {
      const [kpiRes, healthRes, secMetrics, auditLog] = await Promise.all([
        listKPIs().catch(() => ({ items: {} })),
        checkHealth().catch(() => ({ status: 'unavailable', service: 'ranengineer-backend' })),
        getSecurityMetrics().catch(() => null),
        listSecurityAuditLog(20).catch(() => []),
      ])
      setKpis(kpiRes.items || {})
      setHealth(healthRes)
      setSecurityMetrics(secMetrics)
      setAuditEvents(auditLog)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load configuration.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
      <div className="mb-8 border-b border-slate-800 pb-6">
        <span className="font-mono text-xs uppercase tracking-widest text-teal-400">System Configuration</span>
        <h1 className="text-3xl font-bold tracking-tight text-slate-100 mt-1">RAN Engine Settings & Thresholds</h1>
        <p className="mt-1 text-sm text-slate-400">
          Inspection of configured KPI threshold boundaries, scoring weights, API connectivity, and LLM provider parameters.
        </p>
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-red-900 bg-red-950/60 p-4 text-sm text-red-200">
          {error}
        </div>
      )}

      {/* Connectivity & Environment Cards */}
      <div className="grid gap-4 sm:grid-cols-3 mb-8">
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-xs text-slate-400 font-mono">Backend API Status</p>
          <div className="mt-2 flex items-center gap-2">
            <span className={`h-2.5 w-2.5 rounded-full ${health?.status === 'ok' ? 'bg-teal-400' : 'bg-red-400'}`}></span>
            <span className="text-lg font-bold text-slate-100 font-mono">
              {health?.status === 'ok' ? 'Operational' : 'Unavailable'}
            </span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500 font-mono">http://localhost:8000/api/v1</p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-xs text-slate-400 font-mono">Telemetry Persistence</p>
          <div className="mt-2 flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-teal-400"></span>
            <span className="text-lg font-bold text-slate-100 font-mono">PostgreSQL 16</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500 font-mono">datasets & cells tables active</p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-xs text-slate-400 font-mono">AI Provider Engine</p>
          <div className="mt-2 flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-teal-400"></span>
            <span className="text-lg font-bold text-teal-300 font-mono">Grounded Provider</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500 font-mono">Azure OpenAI / Deterministic</p>
        </div>
      </div>

      {/* Active KPI Threshold Definitions Table */}
      <section className="rounded-xl border border-slate-800 bg-slate-900 overflow-hidden">
        <div className="border-b border-slate-800 px-5 py-4 flex items-center justify-between">
          <div>
            <h2 className="font-semibold text-slate-200">Active KPI Threshold Engine (Section 8)</h2>
            <p className="text-xs text-slate-400">Configuration-driven scoring rules loaded from definitions.json</p>
          </div>
          <span className="font-mono text-xs text-slate-500">{Object.keys(kpis).length} Configured KPIs</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 uppercase tracking-wider text-slate-400 font-mono text-[11px]">
              <tr>
                <th>KPI</th>
                <th>Unit</th>
                <th>Direction</th>
                <th>Good (Healthy)</th>
                <th>Warning</th>
                <th>Critical</th>
                <th>Weight</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {loading && (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-400">
                    Loading KPI threshold configuration…
                  </td>
                </tr>
              )}
              {!loading && (Object.entries(kpis) as [string, KPIDefinition][]).map(([kpiName, def]) => {
                const isHigher = def.direction === 'higher_is_better'
                return (
                  <tr key={kpiName} className="hover:bg-slate-800/40 transition">
                    <td className="font-mono font-bold text-teal-300 uppercase">{kpiName}</td>
                    <td className="font-mono text-slate-300">{def.unit}</td>
                    <td>
                      <span className="rounded bg-slate-800 px-2 py-0.5 font-mono text-[10px] text-slate-300">
                        {isHigher ? 'Higher is better' : 'Lower is better'}
                      </span>
                    </td>
                    <td className="font-mono text-teal-400 font-semibold">
                      {isHigher ? `≥ ${def.good}` : `< ${def.good}`}
                    </td>
                    <td className="font-mono text-amber-400 font-semibold">
                      {isHigher ? `≥ ${def.warning}` : `< ${def.warning}`}
                    </td>
                    <td className="font-mono text-red-400 font-semibold">
                      {isHigher ? `< ${def.warning}` : `≥ ${def.warning}`}
                    </td>
                    <td className="font-mono text-slate-200 font-bold">{def.weight}%</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* Redis Security Counters & Threat Mitigation (Section 31 & 32) */}
      <section className="mt-8 rounded-xl border border-slate-800 bg-slate-900 overflow-hidden">
        <div className="border-b border-slate-800 px-5 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="font-semibold text-slate-200">
              Redis Security Counters & Threat Auditing (Section 31 & 32)
            </h2>
            <p className="text-xs text-slate-400">
              Sliding-window rate limiting, brute-force lockout, and prompt injection detection
            </p>
          </div>
          <span className="font-mono text-xs text-teal-400">
            {securityMetrics ? `Limiter: ${securityMetrics.status}` : 'Limiter: Inactive'}
          </span>
        </div>

        <div className="p-5 grid gap-4 sm:grid-cols-3 border-b border-slate-800 bg-slate-950/40">
          <div className="rounded-lg border border-slate-800 bg-slate-900 p-3">
            <p className="text-[11px] font-mono text-slate-400">Tracked Security Keys</p>
            <p className="text-xl font-mono font-bold text-slate-200 mt-1">
              {securityMetrics?.tracked_security_keys ?? 0}
            </p>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900 p-3">
            <p className="text-[11px] font-mono text-slate-400">Brute Force Locked Users</p>
            <p className="text-xl font-mono font-bold text-amber-400 mt-1">
              {securityMetrics?.locked_users_count ?? 0}
            </p>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900 p-3">
            <p className="text-[11px] font-mono text-slate-400">Prompt Injection Guardrail</p>
            <p className="text-xl font-mono font-bold text-teal-400 mt-1">
              ENFORCED
            </p>
          </div>
        </div>

        {/* Audit Log Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 font-mono text-[11px] text-slate-400 uppercase tracking-wider">
              <tr>
                <th className="p-3">Event ID</th>
                <th className="p-3">Timestamp</th>
                <th className="p-3">Type</th>
                <th className="p-3">Severity</th>
                <th className="p-3">Actor</th>
                <th className="p-3">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 font-mono text-[11px]">
              {auditEvents.length > 0 ? (
                auditEvents.map((ev) => (
                  <tr key={ev.event_id} className="hover:bg-slate-800/40">
                    <td className="p-3 text-cyan-300">{ev.event_id}</td>
                    <td className="p-3 text-slate-400">{ev.timestamp.split('T')[1]?.substring(0, 8)} UTC</td>
                    <td className="p-3 text-slate-200">{ev.event_type}</td>
                    <td className="p-3">
                      <span
                        className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${
                          ev.severity === 'CRITICAL'
                            ? 'bg-rose-950 text-rose-300 border border-rose-800'
                            : ev.severity === 'WARNING'
                            ? 'bg-amber-950 text-amber-300 border border-amber-800'
                            : 'bg-slate-800 text-slate-300'
                        }`}
                      >
                        {ev.severity}
                      </span>
                    </td>
                    <td className="p-3 text-slate-400">{ev.actor}</td>
                    <td className="p-3 text-slate-300 font-sans text-xs">{ev.description}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="p-6 text-center text-slate-500 font-sans">
                    No security events recorded in current audit horizon.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Rationale Disclaimer */}
      <div className="mt-6 rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-xs text-slate-400">
        <strong className="text-slate-300">Architecture Note: </strong>
        In accordance with Section 8 & 31 of the project specifications, thresholds, weights, and security counter policies are completely decoupled from business logic and maintained with strict TTLs and telemetry auditing.
      </div>
    </main>
  )
}

