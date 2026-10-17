'use client'

import { useEffect, useState } from 'react'
import {
  DigitalTwinScenarioTemplate,
  ISACPerformance,
  SimulationParameter,
  SimulationResult,
  getISACBenchmark,
  listDigitalTwinScenarios,
  simulateDigitalTwin,
} from '@/lib/api'

export default function DigitalTwinPage() {
  const [scenarios, setScenarios] = useState<DigitalTwinScenarioTemplate[]>([])
  const [loadingScenarios, setLoadingScenarios] = useState(true)
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('scenario-tilt-opt')

  // Parameter State
  const [targetCellId, setTargetCellId] = useState('CELL_001_A')
  const [tiltOffset, setTiltOffset] = useState(2.5)
  const [txPowerOffset, setTxPowerOffset] = useState(0.0)
  const [mimoLayers, setMimoLayers] = useState(4)
  const [frequencyBandGhz, setFrequencyBandGhz] = useState(3.5)
  const [carrierBwMhz, setCarrierBwMhz] = useState(100.0)
  const [isacRatio, setIsacRatio] = useState(0.0)

  // Simulation Results
  const [simulating, setSimulating] = useState(false)
  const [result, setResult] = useState<SimulationResult | null>(null)
  const [isacBenchmarks, setIsacBenchmarks] = useState<ISACPerformance[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadScenariosAndBenchmark()
  }, [])

  async function loadScenariosAndBenchmark() {
    setLoadingScenarios(true)
    setError(null)
    try {
      const [scList, isacList] = await Promise.all([
        listDigitalTwinScenarios(),
        getISACBenchmark().catch(() => []),
      ])
      setScenarios(scList)
      setIsacBenchmarks(isacList)

      // Initial simulation with default scenario
      if (scList.length > 0) {
        applyScenario(scList[0])
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load digital twin resources.')
    } finally {
      setLoadingScenarios(false)
    }
  }

  function applyScenario(sc: DigitalTwinScenarioTemplate) {
    setSelectedScenarioId(sc.id)
    setTargetCellId(sc.sample_cell_id)
    setTiltOffset(sc.recommended_parameters.tilt_offset_deg)
    setTxPowerOffset(sc.recommended_parameters.tx_power_offset_dbm)
    setMimoLayers(sc.recommended_parameters.mimo_layers)
    setFrequencyBandGhz(sc.recommended_parameters.frequency_band_ghz)
    setCarrierBwMhz(sc.recommended_parameters.carrier_bandwidth_mhz)
    setIsacRatio(sc.recommended_parameters.isac_sensing_resource_ratio)
    triggerSimulation({
      tilt_offset_deg: sc.recommended_parameters.tilt_offset_deg,
      tx_power_offset_dbm: sc.recommended_parameters.tx_power_offset_dbm,
      mimo_layers: sc.recommended_parameters.mimo_layers,
      frequency_band_ghz: sc.recommended_parameters.frequency_band_ghz,
      carrier_bandwidth_mhz: sc.recommended_parameters.carrier_bandwidth_mhz,
      isac_sensing_resource_ratio: sc.recommended_parameters.isac_sensing_resource_ratio,
    }, sc.sample_cell_id)
  }

  async function triggerSimulation(params: SimulationParameter, cellId = targetCellId) {
    setSimulating(true)
    setError(null)
    try {
      const res = await simulateDigitalTwin(cellId, params)
      setResult(res)
    } catch (err: any) {
      setError(err?.message || 'Simulation execution failed.')
    } finally {
      setSimulating(false)
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    triggerSimulation({
      tilt_offset_deg: Number(tiltOffset),
      tx_power_offset_dbm: Number(txPowerOffset),
      mimo_layers: Number(mimoLayers),
      frequency_band_ghz: Number(frequencyBandGhz),
      carrier_bandwidth_mhz: Number(carrierBwMhz),
      isac_sensing_resource_ratio: Number(isacRatio),
    })
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      {/* Header & 6G Research Notice */}
      <div className="border-b border-slate-800 pb-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="rounded-full bg-indigo-950 px-3 py-0.5 text-xs font-mono font-medium text-indigo-400 border border-indigo-800">
                6G / IMT-2030 Research Lab
              </span>
              <span className="rounded-full bg-cyan-950 px-3 py-0.5 text-xs font-mono text-cyan-400 border border-cyan-800">
                AI-Native RAN Digital Twin
              </span>
              <span className="rounded-full bg-slate-800 px-3 py-0.5 text-xs font-mono text-slate-300">
                3GPP TR 38.901
              </span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-100 sm:text-3xl">
              RAN Digital Twin & ISAC Simulation Studio
            </h1>
            <p className="mt-1 text-sm text-slate-400 max-w-3xl">
              Deterministic what-if modeling for RF antenna beamforming, sub-THz capacity scaling, and Integrated Sensing & Communications (ISAC) trade-offs before physical network execution.
            </p>
          </div>
        </div>

        {/* Mandatory Research Notice */}
        <div className="mt-5 rounded-lg border border-indigo-500/40 bg-indigo-950/20 p-4">
          <div className="flex items-start gap-3">
            <span className="text-indigo-400 text-lg">🔬</span>
            <div className="text-xs text-indigo-200 leading-relaxed">
              <strong className="font-semibold text-indigo-300">SYNTHETIC RESEARCH MODEL:</strong> Digital twin projections are deterministic mathematical simulations based on 3GPP ray-tracing approximations and IMT-2030 waveform specifications. Certified engineer validation is required before live network deployment.
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-rose-800 bg-rose-950/40 p-4 text-xs text-rose-300">
          {error}
        </div>
      )}

      {/* Benchmark Scenarios Carousel / Cards */}
      <div className="space-y-3">
        <h2 className="text-xs font-mono uppercase tracking-wider text-slate-400">
          Pre-Configured Benchmark Scenarios ({scenarios.length})
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {scenarios.map((sc) => {
            const isSelected = selectedScenarioId === sc.id
            return (
              <div
                key={sc.id}
                onClick={() => applyScenario(sc)}
                className={`cursor-pointer rounded-xl border p-4 transition ${
                  isSelected
                    ? 'border-indigo-500 bg-indigo-950/30 shadow-md shadow-indigo-500/10'
                    : 'border-slate-800 bg-slate-900/60 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between text-[11px] font-mono text-indigo-400 mb-1">
                  <span>{sc.technology}</span>
                  <span className="text-slate-500">{sc.sample_cell_id}</span>
                </div>
                <h3 className="font-semibold text-slate-200 text-xs line-clamp-1">{sc.title}</h3>
                <p className="mt-1.5 text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                  {sc.description}
                </p>
                <div className="mt-3 pt-2.5 border-t border-slate-800/80 text-[10px] text-slate-500 font-mono">
                  {sc.expected_outcome}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Main Workspace: Simulator Controls (Left) + Projected Telemetry (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Parameter Controls (5 cols) */}
        <div className="lg:col-span-5 rounded-xl border border-slate-800 bg-slate-900/40 p-6 space-y-6">
          <div className="border-b border-slate-800 pb-3">
            <h2 className="text-base font-semibold text-slate-100">Digital Twin Parameter Controls</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Adjust RF parameters to evaluate projected physics and health scores.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4 text-xs">
            <div>
              <label className="block text-slate-300 font-medium mb-1">Target Sector / Cell ID</label>
              <input
                type="text"
                value={targetCellId}
                onChange={(e) => setTargetCellId(e.target.value)}
                required
                className="w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 font-mono text-xs focus:border-indigo-500 focus:outline-none"
              />
            </div>

            {/* Electrical Downtilt */}
            <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3.5 space-y-2">
              <div className="flex justify-between text-slate-300">
                <span className="font-medium">Antenna Downtilt:</span>
                <span className="font-mono text-indigo-300">
                  {tiltOffset > 0 ? `+${tiltOffset}` : tiltOffset}°
                </span>
              </div>
              <input
                type="range"
                min={-6.0}
                max={6.0}
                step={0.5}
                value={tiltOffset}
                onChange={(e) => setTiltOffset(Number(e.target.value))}
                className="w-full accent-indigo-400"
              />
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>-6° (Overshoot / Uptilt)</span>
                <span>0° (Boresight)</span>
                <span>+6° (Downtilt)</span>
              </div>
            </div>

            {/* Transmit Power Offset */}
            <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3.5 space-y-2">
              <div className="flex justify-between text-slate-300">
                <span className="font-medium">Tx Power Offset:</span>
                <span className="font-mono text-indigo-300">
                  {txPowerOffset > 0 ? `+${txPowerOffset}` : txPowerOffset} dBm
                </span>
              </div>
              <input
                type="range"
                min={-8.0}
                max={8.0}
                step={1.0}
                value={txPowerOffset}
                onChange={(e) => setTxPowerOffset(Number(e.target.value))}
                className="w-full accent-indigo-400"
              />
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>-8 dBm (Power Saving)</span>
                <span>0 dBm</span>
                <span>+8 dBm (Boost)</span>
              </div>
            </div>

            {/* Frequency & Bandwidth */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-300 font-medium mb-1">Carrier Band</label>
                <select
                  value={frequencyBandGhz}
                  onChange={(e) => setFrequencyBandGhz(Number(e.target.value))}
                  className="w-full rounded border border-slate-700 bg-slate-950 px-2.5 py-1.5 text-slate-100 font-mono focus:border-indigo-500 focus:outline-none"
                >
                  <option value={3.5}>3.5 GHz (5G Mid-band)</option>
                  <option value={28.0}>28.0 GHz (5G mmWave)</option>
                  <option value={140.0}>140.0 GHz (6G Sub-THz D-Band)</option>
                </select>
              </div>
              <div>
                <label className="block text-slate-300 font-medium mb-1">MIMO Layers</label>
                <select
                  value={mimoLayers}
                  onChange={(e) => setMimoLayers(Number(e.target.value))}
                  className="w-full rounded border border-slate-700 bg-slate-950 px-2.5 py-1.5 text-slate-100 font-mono focus:border-indigo-500 focus:outline-none"
                >
                  <option value={4}>4 Layers (SISO/MIMO)</option>
                  <option value={8}>8 Layers (8T8R)</option>
                  <option value={16}>16 Layers (32T32R)</option>
                  <option value={32}>32 Layers (64T64R Massive MIMO)</option>
                  <option value={64}>64 Layers (6G AI-Native)</option>
                </select>
              </div>
            </div>

            {/* Carrier Bandwidth */}
            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>Carrier Bandwidth:</span>
                <span className="font-mono text-indigo-300">{carrierBwMhz} MHz</span>
              </div>
              <input
                type="range"
                min={50}
                max={2000}
                step={50}
                value={carrierBwMhz}
                onChange={(e) => setCarrierBwMhz(Number(e.target.value))}
                className="w-full accent-indigo-400"
              />
            </div>

            {/* 6G ISAC Sensing Slider */}
            <div className="rounded-lg border border-indigo-900/50 bg-indigo-950/30 p-3.5 space-y-2">
              <div className="flex justify-between items-center text-slate-300">
                <span className="font-medium text-indigo-300">6G ISAC Sensing Resource Split:</span>
                <span className="font-mono font-bold text-indigo-400">
                  {Math.round(isacRatio * 100)}%
                </span>
              </div>
              <input
                type="range"
                min={0.0}
                max={0.5}
                step={0.05}
                value={isacRatio}
                onChange={(e) => setIsacRatio(Number(e.target.value))}
                className="w-full accent-indigo-400"
              />
              <p className="text-[10px] text-slate-400 leading-normal">
                {isacRatio === 0
                  ? 'Pure Communication Mode (100% data throughput)'
                  : `Dual-Function Mode: ${Math.round(isacRatio * 100)}% radar environment sensing, ${Math.round((1 - isacRatio) * 100)}% communications.`}
              </p>
            </div>

            <button
              type="submit"
              disabled={simulating}
              className="w-full rounded-md bg-indigo-500 py-2.5 font-semibold text-slate-950 hover:bg-indigo-400 transition disabled:opacity-50"
            >
              {simulating ? 'Computing Ray-Tracing Physics...' : 'Run Digital Twin Simulation'}
            </button>
          </form>
        </div>

        {/* Right Column: Projected Physics & Comparison (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {result ? (
            <div className="space-y-6">
              {/* Health Score Comparison Box */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div>
                    <h3 className="font-bold text-slate-100 text-sm">
                      Simulation Result: {result.target_cell_id}
                    </h3>
                    <p className="text-[11px] text-slate-400 font-mono">
                      ID: {result.simulation_id} | Framework: {result.research_tier}
                    </p>
                  </div>
                  <div className="text-right">
                    <span
                      className={`inline-block rounded-md px-2.5 py-1 text-xs font-mono font-bold ${
                        result.delta_health_score >= 10
                          ? 'bg-teal-950 text-teal-300 border border-teal-700'
                          : result.delta_health_score >= 0
                          ? 'bg-cyan-950 text-cyan-300 border border-cyan-800'
                          : 'bg-rose-950 text-rose-300 border border-rose-800'
                      }`}
                    >
                      {result.delta_health_score >= 0 ? `+${result.delta_health_score}` : result.delta_health_score} pts
                    </span>
                  </div>
                </div>

                {/* Score Meters */}
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
                    <span className="text-[11px] text-slate-500 font-mono uppercase">Baseline Score</span>
                    <p className="text-2xl font-mono font-bold text-slate-300 mt-1">
                      {result.baseline_health_score.toFixed(1)}
                      <span className="text-xs text-slate-500">/100</span>
                    </p>
                  </div>
                  <div className="rounded-lg border border-indigo-900/60 bg-indigo-950/20 p-4">
                    <span className="text-[11px] text-indigo-400 font-mono uppercase">Projected Score</span>
                    <p className="text-2xl font-mono font-bold text-indigo-300 mt-1">
                      {result.projected_health_score.toFixed(1)}
                      <span className="text-xs text-slate-500">/100</span>
                    </p>
                  </div>
                </div>

                {/* Side-by-side Telemetry Table */}
                <div className="overflow-x-auto rounded-lg border border-slate-800">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950 text-slate-400 font-mono text-[11px]">
                      <tr>
                        <th className="p-2.5">KPI Metric</th>
                        <th className="p-2.5">Baseline</th>
                        <th className="p-2.5">Projected</th>
                        <th className="p-2.5">Impact</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 bg-slate-900/30 font-mono text-[11px]">
                      <tr>
                        <td className="p-2.5 text-slate-300 font-sans">Coverage RSRP</td>
                        <td className="p-2.5 text-slate-400">{result.baseline_kpis.RSRP ?? '—'} dBm</td>
                        <td className="p-2.5 text-indigo-300 font-bold">{result.projected_kpis.rsrp_dbm} dBm</td>
                        <td className="p-2.5 text-slate-400">
                          {(result.projected_kpis.rsrp_dbm - (result.baseline_kpis.RSRP ?? -95.0)).toFixed(1)} dBm
                        </td>
                      </tr>
                      <tr>
                        <td className="p-2.5 text-slate-300 font-sans">Radio SINR</td>
                        <td className="p-2.5 text-slate-400">{result.baseline_kpis.SINR ?? '—'} dB</td>
                        <td className="p-2.5 text-indigo-300 font-bold">{result.projected_kpis.sinr_db} dB</td>
                        <td className="p-2.5 text-slate-400">
                          {(result.projected_kpis.sinr_db - (result.baseline_kpis.SINR ?? 5.0)).toFixed(1)} dB
                        </td>
                      </tr>
                      <tr>
                        <td className="p-2.5 text-slate-300 font-sans">DL Throughput</td>
                        <td className="p-2.5 text-slate-400">{result.baseline_kpis.DL_THROUGHPUT ?? '—'} Mbps</td>
                        <td className="p-2.5 text-indigo-300 font-bold">
                          {result.projected_kpis.dl_throughput_mbps > 1000
                            ? `${(result.projected_kpis.dl_throughput_mbps / 1000).toFixed(2)} Gbps`
                            : `${result.projected_kpis.dl_throughput_mbps} Mbps`}
                        </td>
                        <td className="p-2.5 text-teal-400">
                          {result.projected_kpis.dl_throughput_mbps > (result.baseline_kpis.DL_THROUGHPUT ?? 30) ? '▲ Boosted' : '▼ Reduced'}
                        </td>
                      </tr>
                      <tr>
                        <td className="p-2.5 text-slate-300 font-sans">PRB Utilization</td>
                        <td className="p-2.5 text-slate-400">{result.baseline_kpis.PRB_UTILIZATION ?? '—'}%</td>
                        <td className="p-2.5 text-indigo-300 font-bold">{result.projected_kpis.prb_utilization_percent}%</td>
                        <td className="p-2.5 text-slate-400">
                          {(result.projected_kpis.prb_utilization_percent - (result.baseline_kpis.PRB_UTILIZATION ?? 60)).toFixed(1)}%
                        </td>
                      </tr>
                      <tr>
                        <td className="p-2.5 text-slate-300 font-sans">Call Drop Rate</td>
                        <td className="p-2.5 text-slate-400">{result.baseline_kpis.CALL_DROP_RATE ?? '—'}%</td>
                        <td className="p-2.5 text-indigo-300 font-bold">{result.projected_kpis.call_drop_rate_percent}%</td>
                        <td className="p-2.5 text-slate-400">
                          {(result.projected_kpis.call_drop_rate_percent - (result.baseline_kpis.CALL_DROP_RATE ?? 1.0)).toFixed(2)}%
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* 6G ISAC Radar Results Box */}
                {result.isac_performance && result.isac_performance.isac_enabled && (
                  <div className="rounded-xl border border-indigo-800 bg-indigo-950/30 p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-indigo-300 font-mono">
                        📡 6G ISAC Radar Sensing Telemetry
                      </span>
                      <span className="text-[10px] text-indigo-400 font-mono">
                        Resource Split: {Math.round(result.isac_performance.sensing_resource_ratio * 100)}%
                      </span>
                    </div>

                    <div className="grid grid-cols-3 gap-2 text-center text-xs">
                      <div className="rounded bg-slate-950 p-2 border border-slate-800">
                        <span className="text-[10px] text-slate-500 font-mono uppercase">Range Resolution</span>
                        <p className="font-bold text-indigo-300 mt-0.5">
                          {result.isac_performance.sensing_range_resolution_cm} cm
                        </p>
                      </div>
                      <div className="rounded bg-slate-950 p-2 border border-slate-800">
                        <span className="text-[10px] text-slate-500 font-mono uppercase">Velocity Accuracy</span>
                        <p className="font-bold text-indigo-300 mt-0.5">
                          ±{result.isac_performance.sensing_velocity_accuracy_m_per_s} m/s
                        </p>
                      </div>
                      <div className="rounded bg-slate-950 p-2 border border-slate-800">
                        <span className="text-[10px] text-slate-500 font-mono uppercase">Comm Throughput</span>
                        <p className="font-bold text-indigo-300 mt-0.5">
                          {result.isac_performance.communication_throughput_gbps} Gbps
                        </p>
                      </div>
                    </div>

                    <p className="text-[11px] text-indigo-200/90 italic">
                      {result.isac_performance.research_note}
                    </p>
                  </div>
                )}

                {/* AI Recommendation & Risk Assessment */}
                <div className="space-y-3 rounded-lg border border-slate-800 bg-slate-950 p-4 text-xs">
                  <div>
                    <span className="font-semibold text-slate-200">Engineering Recommendation:</span>
                    <p className="text-slate-300 mt-1 leading-relaxed">{result.recommendation}</p>
                  </div>
                  <div>
                    <span className="font-semibold text-slate-200">Risk Assessment:</span>
                    <p className="text-slate-400 mt-1 leading-relaxed font-mono text-[11px]">
                      {result.risk_assessment}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-slate-800 bg-slate-900/20 p-12 text-center text-slate-500 text-xs">
              Configure parameters on the left and trigger a simulation to inspect deterministic digital twin projections.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

