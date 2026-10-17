'use client'

import { useEffect, useState } from 'react'
import {
  A1PolicySchema,
  RAppDescriptor,
  RAppGenerationRequest,
  approveOranRapp,
  generateOranRapp,
  getOranTemplates,
  listOranRapps,
} from '@/lib/api'

export default function OranStudioPage() {
  const [templates, setTemplates] = useState<A1PolicySchema[]>([])
  const [rapps, setRapps] = useState<RAppDescriptor[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Generator form state
  const [selectedPolicyType, setSelectedPolicyType] = useState<
    'traffic_steering' | 'energy_saving' | 'qoe_assurance'
  >('traffic_steering')
  const [rappName, setRappName] = useState('Downtown 5G Traffic Balancer')
  const [targetCells, setTargetCells] = useState('CELL_001_A, CELL_001_B')
  const [targetSite, setTargetSite] = useState('SITE_001')
  const [objective, setObjective] = useState(
    'Offload macro cell PRB congestion to co-located micro cell layer'
  )

  // Policy Parameters
  const [prbThreshold, setPrbThreshold] = useState(80.0)
  const [rsrpOffset, setRsrpOffset] = useState(-4.0)
  const [offpeakPrb, setOffpeakPrb] = useState(15.0)
  const [reactivationPrb, setReactivationPrb] = useState(55.0)
  const [underlayCell, setUnderlayCell] = useState('CELL_UNDERLAY_700M')
  const [minThroughput, setMinThroughput] = useState(50.0)
  const [maxDelayBudget, setMaxDelayBudget] = useState(20.0)

  // Selected rApp for payload inspection
  const [inspectRapp, setInspectRapp] = useState<RAppDescriptor | null>(null)
  const [approvalNotes, setApprovalNotes] = useState('Reviewed in simulation twin. Approved for staging.')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    setError(null)
    try {
      const [tData, rData] = await Promise.all([getOranTemplates(), listOranRapps()])
      setTemplates(tData)
      setRapps(rData)
      if (rData.length > 0) {
        setInspectRapp(rData[0])
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load O-RAN studio data.')
    } finally {
      setLoading(false)
    }
  }

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    setSuccessMsg(null)

    const cellList = targetCells
      .split(',')
      .map((c) => c.trim())
      .filter(Boolean)

    if (cellList.length === 0) {
      setError('At least one target cell ID is required.')
      setSubmitting(false)
      return
    }

    let params: Record<string, any> = {}
    if (selectedPolicyType === 'traffic_steering') {
      params = {
        prb_threshold_percent: Number(prbThreshold),
        rsrp_offset_db: Number(rsrpOffset),
        hysteresis_db: 2.0,
        time_to_trigger_ms: 320,
      }
    } else if (selectedPolicyType === 'energy_saving') {
      params = {
        offpeak_prb_threshold: Number(offpeakPrb),
        reactivation_prb_threshold: Number(reactivationPrb),
        coverage_underlay_cell_id: underlayCell.trim(),
        sleep_depth: 'carrier_shutdown',
      }
    } else if (selectedPolicyType === 'qoe_assurance') {
      params = {
        slice_id: 'SST-1_SD-URLLC01',
        min_throughput_dl_mbps: Number(minThroughput),
        max_packet_delay_budget_ms: Number(maxDelayBudget),
        priority_level: 1,
      }
    }

    const payload: RAppGenerationRequest = {
      rapp_name: rappName.trim(),
      policy_type: selectedPolicyType,
      target_cells: cellList,
      target_site_id: targetSite.trim() || undefined,
      objective: objective.trim(),
      parameters: params,
    }

    try {
      const newRapp = await generateOranRapp(payload)
      setSuccessMsg(`rApp '${newRapp.name}' successfully synthesized with status ${newRapp.review_status}.`)
      setInspectRapp(newRapp)
      await loadData()
    } catch (err: any) {
      setError(err?.message || 'Failed to generate rApp package.')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleApprove(rappId: string) {
    setSubmitting(true)
    setError(null)
    setSuccessMsg(null)
    try {
      const approved = await approveOranRapp(rappId, approvalNotes)
      setSuccessMsg(`rApp '${approved.name}' approved with status ${approved.review_status}.`)
      setInspectRapp(approved)
      await loadData()
    } catch (err: any) {
      setError(err?.message || 'Approval failed.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      {/* Header & Guardrail Notice */}
      <div className="border-b border-slate-800 pb-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="rounded-full bg-cyan-950 px-3 py-0.5 text-xs font-mono font-medium text-cyan-400 border border-cyan-800">
                O-RAN WG2 Non-RT RIC
              </span>
              <span className="rounded-full bg-slate-800 px-3 py-0.5 text-xs font-mono text-slate-300">
                A1-P Declarative Policies
              </span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-100 sm:text-3xl">
              O-RAN Non-RT RIC rApp Studio
            </h1>
            <p className="mt-1 text-sm text-slate-400 max-w-2xl">
              Synthesize, validate, and simulate declarative A1-P policy descriptors for Traffic Steering, Energy Saving, and QoE Assurance.
            </p>
          </div>
          <button
            onClick={loadData}
            className="self-start md:self-auto rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-800"
          >
            Refresh Studio
          </button>
        </div>

        {/* Mandatory Guardrail Banner */}
        <div className="mt-5 rounded-lg border border-amber-500/40 bg-amber-950/20 p-4">
          <div className="flex items-start gap-3">
            <span className="text-amber-400 text-lg">⚠️</span>
            <div className="text-xs text-amber-200 leading-relaxed">
              <strong className="font-semibold text-amber-300">MANDATORY TELECOM GUARDRAIL:</strong> Direct production deployment to live Near-RT RIC is prohibited without certified RAN Engineer sign-off and simulation boundary testing. Analytics calculates, rules interpret, AI explains, engineer decides.
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-rose-800 bg-rose-950/40 p-4 text-xs text-rose-300">
          {error}
        </div>
      )}

      {successMsg && (
        <div className="rounded-lg border border-teal-800 bg-teal-950/40 p-4 text-xs text-teal-300">
          {successMsg}
        </div>
      )}

      {/* Templates Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {templates.map((tpl) => {
          const isSelected =
            (tpl.policy_type_id === 20000 && selectedPolicyType === 'traffic_steering') ||
            (tpl.policy_type_id === 20001 && selectedPolicyType === 'energy_saving') ||
            (tpl.policy_type_id === 20002 && selectedPolicyType === 'qoe_assurance')

          return (
            <div
              key={tpl.policy_type_id}
              onClick={() => {
                if (tpl.policy_type_id === 20000) setSelectedPolicyType('traffic_steering')
                if (tpl.policy_type_id === 20001) setSelectedPolicyType('energy_saving')
                if (tpl.policy_type_id === 20002) setSelectedPolicyType('qoe_assurance')
              }}
              className={`cursor-pointer rounded-xl border p-5 transition ${
                isSelected
                  ? 'border-cyan-500 bg-cyan-950/20 shadow-md shadow-cyan-500/10'
                  : 'border-slate-800 bg-slate-900/60 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between text-xs font-mono text-cyan-400 mb-2">
                <span>Type #{tpl.policy_type_id}</span>
                <span className="text-slate-500 text-[11px]">{tpl.standard_reference}</span>
              </div>
              <h3 className="font-semibold text-slate-100 text-sm">{tpl.policy_type_name.replace(/_/g, ' ')}</h3>
              <p className="mt-2 text-xs text-slate-400 line-clamp-3 leading-relaxed">
                {tpl.description}
              </p>
              <div className="mt-4 flex items-center justify-between pt-3 border-t border-slate-800/80 text-[11px]">
                <span className="text-slate-400">Parameters:</span>
                <span className="font-mono text-cyan-300">
                  {Object.keys(tpl.default_parameters).length} configured
                </span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Main Studio Grid: Synthesizer Form + rApp Inspection */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left: Generator Form (5 cols) */}
        <div className="lg:col-span-5 rounded-xl border border-slate-800 bg-slate-900/40 p-6 space-y-6">
          <div>
            <h2 className="text-base font-semibold text-slate-100">Synthesize New rApp Package</h2>
            <p className="text-xs text-slate-400 mt-1">
              Configure parameters conforming to O-RAN WG2 declarative schemas.
            </p>
          </div>

          <form onSubmit={handleGenerate} className="space-y-4 text-xs">
            <div>
              <label className="block text-slate-300 font-medium mb-1">rApp Name</label>
              <input
                type="text"
                value={rappName}
                onChange={(e) => setRappName(e.target.value)}
                required
                className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 focus:border-cyan-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1">Policy Type</label>
              <select
                value={selectedPolicyType}
                onChange={(e: any) => setSelectedPolicyType(e.target.value)}
                className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 focus:border-cyan-500 focus:outline-none"
              >
                <option value="traffic_steering">Traffic Steering (Type 20000)</option>
                <option value="energy_saving">Energy Saving (Type 20001)</option>
                <option value="qoe_assurance">QoE Assurance (Type 20002)</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-300 font-medium mb-1">Target Cells (CSV)</label>
                <input
                  type="text"
                  value={targetCells}
                  onChange={(e) => setTargetCells(e.target.value)}
                  placeholder="CELL_01, CELL_02"
                  required
                  className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 focus:border-cyan-500 focus:outline-none font-mono text-[11px]"
                />
              </div>
              <div>
                <label className="block text-slate-300 font-medium mb-1">Site ID</label>
                <input
                  type="text"
                  value={targetSite}
                  onChange={(e) => setTargetSite(e.target.value)}
                  placeholder="SITE_001"
                  className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 focus:border-cyan-500 focus:outline-none font-mono text-[11px]"
                />
              </div>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1">Objective</label>
              <textarea
                value={objective}
                onChange={(e) => setObjective(e.target.value)}
                rows={2}
                className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 focus:border-cyan-500 focus:outline-none"
              />
            </div>

            {/* Dynamic Parameters Based on Policy */}
            <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4 space-y-3">
              <span className="font-mono text-[11px] uppercase tracking-wider text-cyan-400">
                A1-P Parameters ({selectedPolicyType.replace(/_/g, ' ')})
              </span>

              {selectedPolicyType === 'traffic_steering' && (
                <>
                  <div>
                    <div className="flex justify-between text-slate-300 mb-1">
                      <span>PRB Trigger Threshold:</span>
                      <span className="font-mono text-cyan-300">{prbThreshold}%</span>
                    </div>
                    <input
                      type="range"
                      min={50}
                      max={95}
                      step={1}
                      value={prbThreshold}
                      onChange={(e) => setPrbThreshold(Number(e.target.value))}
                      className="w-full accent-cyan-400"
                    />
                  </div>
                  <div>
                    <div className="flex justify-between text-slate-300 mb-1">
                      <span>RSRP Offset:</span>
                      <span className="font-mono text-cyan-300">{rsrpOffset} dB</span>
                    </div>
                    <input
                      type="range"
                      min={-12}
                      max={12}
                      step={0.5}
                      value={rsrpOffset}
                      onChange={(e) => setRsrpOffset(Number(e.target.value))}
                      className="w-full accent-cyan-400"
                    />
                  </div>
                </>
              )}

              {selectedPolicyType === 'energy_saving' && (
                <>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-slate-400 block mb-1">Off-peak PRB (%):</label>
                      <input
                        type="number"
                        value={offpeakPrb}
                        onChange={(e) => setOffpeakPrb(Number(e.target.value))}
                        className="w-full rounded border border-slate-700 bg-slate-900 px-2 py-1 text-slate-100 font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-slate-400 block mb-1">Reactivation PRB (%):</label>
                      <input
                        type="number"
                        value={reactivationPrb}
                        onChange={(e) => setReactivationPrb(Number(e.target.value))}
                        className="w-full rounded border border-slate-700 bg-slate-900 px-2 py-1 text-slate-100 font-mono"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="text-slate-400 block mb-1">Mandatory Underlay Cell:</label>
                    <input
                      type="text"
                      value={underlayCell}
                      onChange={(e) => setUnderlayCell(e.target.value)}
                      placeholder="CELL_UNDERLAY_ANCHOR"
                      required
                      className="w-full rounded border border-slate-700 bg-slate-900 px-2 py-1 text-slate-100 font-mono text-[11px]"
                    />
                  </div>
                </>
              )}

              {selectedPolicyType === 'qoe_assurance' && (
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-slate-400 block mb-1">Min Throughput (Mbps):</label>
                    <input
                      type="number"
                      value={minThroughput}
                      onChange={(e) => setMinThroughput(Number(e.target.value))}
                      className="w-full rounded border border-slate-700 bg-slate-900 px-2 py-1 text-slate-100 font-mono"
                    />
                  </div>
                  <div>
                    <label className="text-slate-400 block mb-1">Max Delay Budget (ms):</label>
                    <input
                      type="number"
                      value={maxDelayBudget}
                      onChange={(e) => setMaxDelayBudget(Number(e.target.value))}
                      className="w-full rounded border border-slate-700 bg-slate-900 px-2 py-1 text-slate-100 font-mono"
                    />
                  </div>
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-md bg-cyan-500 py-2.5 font-semibold text-slate-950 hover:bg-cyan-400 transition disabled:opacity-50"
            >
              {submitting ? 'Synthesizing rApp Package...' : 'Synthesize Declarative rApp Package'}
            </button>
          </form>
        </div>

        {/* Right: rApp Catalog & Inspector (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-100">
              O-RAN rApp Catalog ({rapps.length})
            </h2>
            <span className="text-xs text-slate-400 font-mono">Status: Monitored</span>
          </div>

          <div className="grid grid-cols-1 gap-3 max-h-[320px] overflow-y-auto pr-1">
            {rapps.map((r) => {
              const isSelected = inspectRapp?.id === r.id
              return (
                <div
                  key={r.id}
                  onClick={() => setInspectRapp(r)}
                  className={`cursor-pointer rounded-lg border p-4 transition flex items-center justify-between ${
                    isSelected
                      ? 'border-cyan-500 bg-cyan-950/30'
                      : 'border-slate-800 bg-slate-900/60 hover:border-slate-700'
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-200 text-xs">{r.name}</span>
                      <span className="font-mono text-[10px] text-slate-500">{r.id}</span>
                    </div>
                    <p className="text-[11px] text-slate-400">
                      Target: <span className="font-mono text-cyan-300">{r.target_cells.join(', ')}</span>
                    </p>
                  </div>
                  <div className="text-right space-y-1">
                    <span
                      className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-mono font-medium ${
                        r.review_status === 'ENGINEER_APPROVED'
                          ? 'bg-teal-950 text-teal-300 border border-teal-700'
                          : r.review_status === 'VALIDATED'
                          ? 'bg-cyan-950 text-cyan-300 border border-cyan-800'
                          : 'bg-amber-950 text-amber-300 border border-amber-800'
                      }`}
                    >
                      {r.review_status}
                    </span>
                    <p className="text-[10px] text-slate-500 font-mono capitalize">
                      {r.policy_type.replace(/_/g, ' ')}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Inspector Panel */}
          {inspectRapp && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h3 className="font-bold text-slate-100 text-sm">{inspectRapp.name}</h3>
                  <p className="text-xs text-slate-400 font-mono">
                    ID: {inspectRapp.id} | Vendor: {inspectRapp.vendor} | Version: {inspectRapp.version}
                  </p>
                </div>
                <div className="text-right">
                  <span
                    className={`inline-block rounded-md px-2.5 py-1 text-xs font-mono font-bold ${
                      inspectRapp.review_status === 'ENGINEER_APPROVED'
                        ? 'bg-teal-950 text-teal-300 border border-teal-700'
                        : 'bg-cyan-950 text-cyan-300 border border-cyan-800'
                    }`}
                  >
                    {inspectRapp.review_status}
                  </span>
                </div>
              </div>

              {/* Guardrail Check Results */}
              <div className="grid grid-cols-3 gap-2 text-center text-xs">
                <div className="rounded bg-slate-950/80 p-2 border border-slate-800">
                  <p className="text-[10px] text-slate-500 font-mono uppercase">Schema Check</p>
                  <p className="font-semibold text-teal-400 mt-0.5">
                    {inspectRapp.guardrail_validation.schema_check ? 'PASSED' : 'FAILED'}
                  </p>
                </div>
                <div className="rounded bg-slate-950/80 p-2 border border-slate-800">
                  <p className="text-[10px] text-slate-500 font-mono uppercase">KPI Bounds</p>
                  <p className="font-semibold text-teal-400 mt-0.5">
                    {inspectRapp.guardrail_validation.kpi_bounds_check ? 'WITHIN LIMITS' : 'FAILED'}
                  </p>
                </div>
                <div className="rounded bg-slate-950/80 p-2 border border-slate-800">
                  <p className="text-[10px] text-slate-500 font-mono uppercase">Telecom Safety</p>
                  <p className="font-semibold text-teal-400 mt-0.5">
                    {inspectRapp.guardrail_validation.guardrail_check ? 'ENFORCED' : 'FAILED'}
                  </p>
                </div>
              </div>

              {/* A1-P Policy Payload JSON Preview */}
              <div>
                <p className="text-xs font-medium text-slate-300 mb-1.5">
                  A1-P Declarative Policy Descriptor (O-RAN WG2 Standard)
                </p>
                <pre className="max-h-48 overflow-y-auto rounded-lg border border-slate-800 bg-slate-950 p-3 text-[11px] font-mono text-cyan-300">
                  {JSON.stringify(inspectRapp.a1_policy_payload, null, 2)}
                </pre>
              </div>

              {/* Telemetry Requirements */}
              <div>
                <p className="text-xs font-medium text-slate-300 mb-1">
                  Required Data Ingestion Streams (Non-RT RIC Analytics)
                </p>
                <ul className="list-disc list-inside text-xs text-slate-400 space-y-0.5">
                  {inspectRapp.data_requirements.map((req, idx) => (
                    <li key={idx}>{req}</li>
                  ))}
                </ul>
              </div>

              {/* Engineer Sign-off & Approval Section */}
              <div className="rounded-lg border border-cyan-900/40 bg-cyan-950/20 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-cyan-300">
                    RAN Engineer Sign-Off & Approval
                  </span>
                  {inspectRapp.approved_by && (
                    <span className="text-[11px] text-teal-400 font-mono">
                      Approved by {inspectRapp.approved_by}
                    </span>
                  )}
                </div>

                {inspectRapp.review_status !== 'ENGINEER_APPROVED' ? (
                  <div className="space-y-2">
                    <input
                      type="text"
                      value={approvalNotes}
                      onChange={(e) => setApprovalNotes(e.target.value)}
                      placeholder="Enter verification notes (e.g. Lab tested on digital twin)..."
                      className="w-full rounded border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-slate-100 font-mono"
                    />
                    <button
                      onClick={() => handleApprove(inspectRapp.id)}
                      disabled={submitting}
                      className="rounded bg-teal-400 px-4 py-1.5 text-xs font-semibold text-slate-950 hover:bg-teal-300 transition"
                    >
                      Authorize & Sign Off rApp Package
                    </button>
                  </div>
                ) : (
                  <p className="text-xs text-teal-300 italic">
                    ✓ Formal engineer approval recorded. This rApp package is certified for staged lab deployment.
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

