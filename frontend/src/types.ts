export type LifecycleState = 'ACTIVE' | 'DEPRECATED' | 'ZOMBIE' | 'DECOMMISSIONED'

export interface ApiInventoryItem {
  id: string
  organization: string
  service_name: string
  http_method: string
  endpoint_path: string
  host: string
  version: string
  source: string
  sources: string[]
  owner: string | null
  is_registered: boolean
  is_documented: boolean
  is_deprecated: boolean
  is_removed_from_supported_surface: boolean
  first_seen: string
  last_seen: string
  lifecycle_state: LifecycleState
  classification_reason: string | null
  classified_at: string | null
  risk_score: number | null
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | null
  risk_features: Record<string, unknown>
  risk_findings: string[]
  risk_explanation: string | null
  risk_assessed_at: string | null
  technology_components: { name: string; version: string; evidence_source: string }[]
  threat_finding_count: number
  simulation_finding_count: number
  created_at: string
  updated_at: string
}

export interface DiscoveryResponse {
  source: string
  discovered_count: number
  added_count: number
  records: ApiInventoryItem[]
}

export interface RiskAssessmentRunResponse {
  total_assessed: number
  low: number
  medium: number
  high: number
  critical: number
  model_training_data: string
  results: { api: ApiInventoryItem; assessed_at: string }[]
}
