const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1'

export interface CellAnalysis {
  cell_id: string
  site_id?: string
  technology?: string
  health_score: number | null
  status: string
  kpis?: Record<string, number | null>
  kpi_statuses?: Record<string, string>
  issues: string[]
  probable_causes: {
    probable_cause: string
    recommended_checks?: string[]
  }[]
}

export interface DatasetSummary {
  total_cells: number
  healthy_cells: number
  warning_cells: number
  critical_cells: number
  unknown_cells?: number
  average_health_score: number | null
}

export interface DatasetAnalysis {
  id: string
  name: string
  filename: string
  technology?: string
  created_at?: string
  row_count?: number
  cell_count?: number
  available_kpis: string[]
  unsupported_columns: string[]
  invalid_values: Record<string, any>[]
  summary: DatasetSummary
  cells: CellAnalysis[]
}

export interface CellAnalysisReport {
  cell_id: string
  site_id?: string
  technology?: string
  health_score: number | null
  status: string
  kpis: Record<string, number | null>
  kpi_statuses: Record<string, string>
  issues: string[]
  probable_causes: {
    probable_cause: string
    recommended_checks: string[]
  }[]
  recommended_checks: string[]
  summary: string
  limitations: string
}

export interface ChatResponse {
  mode: string
  intent: string
  tool_called: string
  evidence: Record<string, any>
  answer: string
  guardrail_report?: {
    is_grounded: boolean
    violations: string[]
    warnings: string[]
  }
  warning?: string
}

export interface KPIDefinition {
  aliases: string[]
  unit: string
  direction: string
  good: number
  warning: number
  weight: number
}

// API functions
export async function listDatasets(): Promise<DatasetAnalysis[]> {
  const res = await fetch(`${API_BASE_URL}/datasets`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch datasets.')
  return res.json()
}

export async function getDataset(id: string): Promise<DatasetAnalysis> {
  const res = await fetch(`${API_BASE_URL}/datasets/${id}`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`Failed to fetch dataset ${id}.`)
  return res.json()
}

export async function getDatasetSummary(id: string): Promise<Record<string, any>> {
  const res = await fetch(`${API_BASE_URL}/datasets/${id}/summary`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`Failed to fetch summary for dataset ${id}.`)
  return res.json()
}

export async function getDatasetCells(id: string, limit = 100): Promise<{ items: CellAnalysis[]; total: number }> {
  const res = await fetch(`${API_BASE_URL}/datasets/${id}/cells?limit=${limit}`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`Failed to fetch cells for dataset ${id}.`)
  return res.json()
}

export async function getBadCells(
  id: string,
  limit = 10,
  status?: string,
  kpi?: string
): Promise<{ items: CellAnalysis[]; total: number }> {
  const params = new URLSearchParams({ limit: String(limit) })
  if (status) params.set('status', status)
  if (kpi) params.set('kpi', kpi)
  const res = await fetch(`${API_BASE_URL}/datasets/${id}/bad-cells?${params.toString()}`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch underperforming cells.')
  return res.json()
}

export async function getDatasetAnomalies(id: string): Promise<{ items: CellAnalysis[]; total: number }> {
  const res = await fetch(`${API_BASE_URL}/datasets/${id}/anomalies`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`Failed to fetch anomalies for dataset ${id}.`)
  return res.json()
}

export async function getCell(cellId: string): Promise<CellAnalysis> {
  const res = await fetch(`${API_BASE_URL}/cells/${encodeURIComponent(cellId)}`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`Cell ${cellId} was not found.`)
  return res.json()
}

export async function getCellAnalysis(cellId: string): Promise<CellAnalysisReport> {
  const res = await fetch(`${API_BASE_URL}/cells/${encodeURIComponent(cellId)}/analysis`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`Analysis for cell ${cellId} was not found.`)
  return res.json()
}

export async function listAnomalies(limit = 50, datasetId?: string): Promise<{ items: CellAnalysis[]; total: number }> {
  const params = new URLSearchParams({ limit: String(limit) })
  if (datasetId) params.set('dataset_id', datasetId)
  const res = await fetch(`${API_BASE_URL}/anomalies?${params.toString()}`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch network anomalies.')
  return res.json()
}

export async function listKPIs(): Promise<{ items: Record<string, KPIDefinition> }> {
  const res = await fetch(`${API_BASE_URL}/kpis`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch KPI definitions.')
  return res.json()
}

export async function uploadDataset(file: File, technology?: string): Promise<DatasetAnalysis> {
  const form = new FormData()
  form.append('file', file)
  if (technology) form.append('technology', technology)
  const response = await fetch(`${API_BASE_URL}/datasets/upload`, { method: 'POST', body: form })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.error?.message ?? body?.detail?.error?.message ?? 'The CSV could not be analyzed.')
  }
  return response.json()
}

export async function askQuestion(datasetId: string, question: string): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dataset_id: datasetId, question }),
  })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.error?.message ?? body?.detail?.error?.message ?? 'Chat failed.')
  }
  return response.json()
}

export async function checkHealth(): Promise<{ status: string; service: string }> {
  const res = await fetch(`${API_BASE_URL}/health`, { cache: 'no-store' })
  if (!res.ok) throw new Error('API service unavailable')
  return res.json()
}

// ── Phase 2 Alarms, Incidents & Correlation APIs ──────────────────────────

export interface AlarmItem {
  alarm_id: string
  site_id?: string | null
  cell_id?: string | null
  technology?: string | null
  alarm_type: string
  severity: string
  status: string
  started_at: string
  ended_at?: string | null
  description: string
  source: string
  metadata?: Record<string, any>
}

export interface IncidentItem {
  id: string
  title: string
  description: string
  severity: string
  status: string
  created_at: string
  updated_at?: string | null
  resolution?: string | null
  affected_cells: string[]
  related_alarms: string[]
}

export interface CellRcaResponse {
  cell_id: string
  site_id?: string | null
  technology?: string | null
  health_score: number | null
  status: string
  kpis: Record<string, number | null>
  kpi_statuses: Record<string, string>
  probable_causes: Record<string, any>[]
  correlated_alarms: {
    alarm_id: string
    alarm_type: string
    severity: string
    status: string
    description: string
    matched_kpis: string[]
    confidence: string
    rationale: string
  }[]
  primary_hypothesis?: string | null
  recommended_actions: string[]
  correlation_summary: string
  disclaimer: string
}

export async function listAlarms(): Promise<AlarmItem[]> {
  const res = await fetch(`${API_BASE_URL}/alarms`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch alarms.')
  return res.json()
}

export async function listActiveAlarms(): Promise<AlarmItem[]> {
  const res = await fetch(`${API_BASE_URL}/alarms/active`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch active alarms.')
  return res.json()
}

export async function listIncidents(): Promise<IncidentItem[]> {
  const res = await fetch(`${API_BASE_URL}/incidents`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch incidents.')
  return res.json()
}

export async function createIncident(data: {
  title: string
  description: string
  severity: string
  affected_cells?: string[]
  related_alarms?: string[]
}): Promise<IncidentItem> {
  const res = await fetch(`${API_BASE_URL}/incidents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error('Failed to create incident.')
  return res.json()
}

export async function resolveIncident(incidentId: string, resolution: string): Promise<IncidentItem> {
  const res = await fetch(`${API_BASE_URL}/incidents/${encodeURIComponent(incidentId)}/resolve`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ resolution }),
  })
  if (!res.ok) throw new Error('Failed to resolve incident.')
  return res.json()
}

export async function getCellRca(cellId: string): Promise<CellRcaResponse> {
  const res = await fetch(`${API_BASE_URL}/cells/${encodeURIComponent(cellId)}/rca`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`RCA for cell ${cellId} was not found.`)
  return res.json()
}

// ── Phase 3 Time-Series Trends & Predictive APIs ──────────────────────────

export interface KpiTrendPoint {
  dataset_id: string
  timestamp: string
  value: number | null
  status?: string | null
}

export interface CellKpiTrendItem {
  kpi_name: string
  points: KpiTrendPoint[]
  trend_direction: 'IMPROVING' | 'DEGRADING' | 'STABLE'
  slope: number
  percentage_change: number
  summary: string
}

export interface CellTrendsResponse {
  cell_id: string
  site_id?: string | null
  technology?: string | null
  data_points_count: number
  trends: Record<string, CellKpiTrendItem>
  overall_health_trend: 'IMPROVING' | 'DEGRADING' | 'STABLE'
  summary: string
}

export interface PredictiveAnomalyItem {
  cell_id: string
  site_id?: string | null
  technology?: string | null
  kpi_name: string
  current_value: number
  projected_value: number
  velocity_rate: number
  risk_level: 'HIGH_RISK' | 'MEDIUM_RISK' | 'LOW_RISK'
  projected_breach_condition: string
  recommended_action: string
  summary: string
}

export interface PredictiveReportResponse {
  total_evaluated_cells: number
  at_risk_cells_count: number
  items: PredictiveAnomalyItem[]
  methodology: string
}

export async function getCellTrends(cellId: string): Promise<CellTrendsResponse> {
  const res = await fetch(`${API_BASE_URL}/cells/${encodeURIComponent(cellId)}/trends`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`Trends for cell ${cellId} were not found.`)
  return res.json()
}

export async function getPredictiveAnomalies(): Promise<PredictiveReportResponse> {
  const res = await fetch(`${API_BASE_URL}/anomalies/predictive`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch predictive anomalies.')
  return res.json()
}

// ── Phase 4 RAG & Multi-Agent APIs ─────────────────────────────────────────

export interface KnowledgeDocItem {
  id: string
  title: string
  domain: string
  keywords: string[]
  source: string
  content: string
  relevance_score: number
}

export interface KnowledgeSearchResponse {
  query: string
  total_matched: number
  documents: KnowledgeDocItem[]
  disclaimer: string
}

export interface AgentContributionItem {
  role: string
  agent_name: string
  status: string
  findings: string[]
  metrics_evaluated: Record<string, any>
  recommendations: string[]
}

export interface MultiAgentReportResponse {
  investigation_id: string
  target_cell_id: string
  target_site_id?: string | null
  health_score?: number | null
  overall_verdict: string
  agent_contributions: AgentContributionItem[]
  consolidated_remediations: string[]
  standards_references: string[]
  engineer_disclaimer: string
}

export async function searchKnowledge(query: string, limit = 3): Promise<KnowledgeSearchResponse> {
  const params = new URLSearchParams({ q: query, limit: String(limit) })
  const res = await fetch(`${API_BASE_URL}/knowledge/search?${params.toString()}`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to search telecom knowledge base.')
  return res.json()
}

export async function investigateCellMultiAgent(cellId: string): Promise<MultiAgentReportResponse> {
  const res = await fetch(`${API_BASE_URL}/agents/investigate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ cell_id: cellId }),
  })
  if (!res.ok) throw new Error(`Multi-agent investigation for cell ${cellId} failed.`)
  return res.json()
}

// ── Phase 6 RBAC, O-RAN Non-RT RIC rApp Studio, & Shift Handover APIs ───────

export type UserRole = 'ADMIN' | 'RAN_ENGINEER' | 'VIEWER'

export interface User {
  id: string
  username: string
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
  permissions: string[]
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in_seconds: number
  user: User
}

export interface A1PolicySchema {
  policy_type_id: number
  policy_type_name: string
  description: string
  standard_reference: string
  json_schema: Record<string, any>
  default_parameters: Record<string, any>
}

export interface RAppValidationResult {
  is_valid: boolean
  schema_check: boolean
  kpi_bounds_check: boolean
  guardrail_check: boolean
  warnings: string[]
  errors: string[]
}

export interface RAppDescriptor {
  id: string
  name: string
  version: string
  vendor: string
  policy_type: 'traffic_steering' | 'energy_saving' | 'qoe_assurance'
  review_status: 'DRAFT' | 'VALIDATED' | 'SIMULATION_TESTED' | 'ENGINEER_APPROVED' | 'REJECTED'
  target_cells: string[]
  target_site_id?: string | null
  objective: string
  a1_policy_payload: Record<string, any>
  data_requirements: string[]
  guardrail_validation: RAppValidationResult
  engineer_notes?: string | null
  approved_by?: string | null
  approved_at?: string | null
  created_at: string
  updated_at: string
  safety_notice: string
}

export interface RAppGenerationRequest {
  rapp_name: string
  policy_type: 'traffic_steering' | 'energy_saving' | 'qoe_assurance'
  target_cells: string[]
  target_site_id?: string | null
  objective?: string
  parameters?: Record<string, any>
  notes?: string | null
}

export interface ShiftHandoverReport {
  report_id: string
  generated_at: string
  shift_title: string
  prepared_by: string
  system_status: 'HEALTHY' | 'DEGRADED' | 'CRITICAL'
  dataset_id?: string | null
  dataset_name?: string | null
  total_cells_monitored: number
  degraded_cell_count: number
  critical_cells: {
    cell_id: string
    site_id?: string | null
    technology?: string | null
    health_score: number
    status: string
    top_issue?: string | null
    probable_causes: string[]
  }[]
  active_alarms: {
    id: string
    site_id?: string | null
    cell_id?: string | null
    severity: string
    alarm_type: string
    description: string
    started_at?: string | null
  }[]
  open_incidents: {
    id: string
    title: string
    severity: string
    status: string
    affected_cells: string[]
    related_alarms: string[]
  }[]
  predictive_warnings: {
    cell_id: string
    kpi_name: string
    velocity_per_hour: number
    projected_value: number
    eta_critical_hours: number
    recommendation: string
  }[]
  oran_rapps: {
    id: string
    name: string
    policy_type: string
    review_status: string
    target_cells: string[]
  }[]
  handover_action_items: string[]
  executive_summary: string
}

export async function loginUser(email: string, password = 'telecom123!'): Promise<TokenResponse> {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) throw new Error('Authentication failed.')
  return res.json()
}

export async function listDemoUsers(): Promise<User[]> {
  const res = await fetch(`${API_BASE_URL}/auth/users`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch user profiles.')
  return res.json()
}

export async function getOranTemplates(): Promise<A1PolicySchema[]> {
  const res = await fetch(`${API_BASE_URL}/oran/templates`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch O-RAN A1 policy templates.')
  return res.json()
}

export async function listOranRapps(policyType?: string): Promise<RAppDescriptor[]> {
  const url = policyType
    ? `${API_BASE_URL}/oran/rapps?policy_type=${encodeURIComponent(policyType)}`
    : `${API_BASE_URL}/oran/rapps`
  const res = await fetch(url, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch O-RAN rApps.')
  return res.json()
}

export async function generateOranRapp(
  payload: RAppGenerationRequest,
  token?: string
): Promise<RAppDescriptor> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(`${API_BASE_URL}/oran/rapps/generate`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err?.error?.message || 'Failed to synthesize O-RAN rApp package.')
  }
  return res.json()
}

export async function approveOranRapp(
  rappId: string,
  notes: string,
  token?: string
): Promise<RAppDescriptor> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(`${API_BASE_URL}/oran/rapps/${encodeURIComponent(rappId)}/approve`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ notes }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err?.error?.message || 'Failed to record engineer approval.')
  }
  return res.json()
}

export async function getShiftHandoverReport(datasetId?: string): Promise<ShiftHandoverReport> {
  const url = datasetId
    ? `${API_BASE_URL}/reports/handover?dataset_id=${encodeURIComponent(datasetId)}`
    : `${API_BASE_URL}/reports/handover`
  const res = await fetch(url, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to generate shift handover report.')
  return res.json()
}

export function getShiftHandoverExportUrl(datasetId?: string): string {
  return datasetId
    ? `${API_BASE_URL}/reports/handover/export?dataset_id=${encodeURIComponent(datasetId)}`
    : `${API_BASE_URL}/reports/handover/export`
}

// ── Phase 7 6G / IMT-2030 Digital Twin & Security Threat Monitoring APIs ──

export interface SimulationParameter {
  tilt_offset_deg: number
  tx_power_offset_dbm: number
  mimo_layers: number
  frequency_band_ghz: number
  carrier_bandwidth_mhz: number
  isac_sensing_resource_ratio: number
}

export interface ProjectedKpis {
  rsrp_dbm: number
  sinr_db: number
  dl_throughput_mbps: number
  ul_throughput_mbps: number
  prb_utilization_percent: number
  call_drop_rate_percent: number
  availability_percent: number
}

export interface ISACPerformance {
  isac_enabled: boolean
  sensing_range_resolution_cm: number
  sensing_velocity_accuracy_m_per_s: number
  sensing_detection_probability: number
  communication_throughput_gbps: number
  sensing_resource_ratio: number
  research_note: string
}

export interface SimulationResult {
  simulation_id: string
  target_cell_id: string
  created_at: string
  parameters: SimulationParameter
  baseline_kpis: Record<string, number>
  baseline_health_score: number
  projected_kpis: ProjectedKpis
  projected_health_score: number
  delta_health_score: number
  isac_performance?: ISACPerformance | null
  projected_status: string
  recommendation: string
  risk_assessment: string
  is_synthetic: boolean
  research_tier: string
  disclaimer: string
}

export interface DigitalTwinScenarioTemplate {
  id: string
  title: string
  description: string
  technology: string
  sample_cell_id: string
  recommended_parameters: SimulationParameter
  expected_outcome: string
}

export interface SecurityMetrics {
  locked_users_count: number
  locked_users: string[]
  tracked_security_keys: number
  status: string
}

export interface SecurityAuditEvent {
  event_id: string
  timestamp: string
  event_type: string
  severity: string
  actor: string
  description: string
  details: Record<string, any>
}

export interface PromptInspectionResult {
  is_safe: boolean
  threat_detected?: string | null
  risk_score: number
  matched_pattern?: string | null
  sanitized_text: string
}

export async function listDigitalTwinScenarios(): Promise<DigitalTwinScenarioTemplate[]> {
  const res = await fetch(`${API_BASE_URL}/digital-twin/scenarios`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch digital twin scenarios.')
  return res.json()
}

export async function simulateDigitalTwin(
  cellId: string,
  parameters: SimulationParameter,
  token?: string
): Promise<SimulationResult> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(`${API_BASE_URL}/digital-twin/simulate`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ cell_id: cellId, parameters }),
  })
  if (!res.ok) throw new Error('Digital twin simulation failed.')
  return res.json()
}

export async function getISACBenchmark(): Promise<ISACPerformance[]> {
  const res = await fetch(`${API_BASE_URL}/digital-twin/isac/benchmark`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch ISAC benchmark curve.')
  return res.json()
}

export async function getSecurityMetrics(): Promise<SecurityMetrics> {
  const res = await fetch(`${API_BASE_URL}/security/metrics`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch security metrics.')
  return res.json()
}

export async function listSecurityAuditLog(limit = 50, severity?: string): Promise<SecurityAuditEvent[]> {
  const url = severity
    ? `${API_BASE_URL}/security/audit-log?limit=${limit}&severity=${encodeURIComponent(severity)}`
    : `${API_BASE_URL}/security/audit-log?limit=${limit}`
  const res = await fetch(url, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch security audit log.')
  return res.json()
}

export async function inspectPrompt(prompt: string): Promise<PromptInspectionResult> {
  const res = await fetch(`${API_BASE_URL}/security/inspect-prompt`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt }),
  })
  if (!res.ok) throw new Error('Prompt inspection failed.')
  return res.json()
}


