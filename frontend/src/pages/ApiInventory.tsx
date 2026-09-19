import type { ApiInventoryItem } from '../types'
import { runClassification, runRiskAssessments } from '../api'
import { useState } from 'react'

interface ApiInventoryProps {
  apis: ApiInventoryItem[]
  loading: boolean
  error: string | null
}

export function ApiInventory({ apis, loading, error }: ApiInventoryProps) {
  const [summary, setSummary] = useState<string | null>(null)
  const [riskSummary, setRiskSummary] = useState<string | null>(null)
  const [running, setRunning] = useState(false)
  const [assessing, setAssessing] = useState(false)

  const classify = async () => {
    setRunning(true)
    try {
      const result = await runClassification()
      setSummary(`Active ${result.active} | Deprecated ${result.deprecated} | Zombie ${result.zombie} | Decommissioned ${result.decommissioned}`)
      window.location.reload()
    } finally { setRunning(false) }
  }

  const assessRisk = async () => {
    setAssessing(true)
    try {
      const result = await runRiskAssessments()
      setRiskSummary(`Assessed ${result.total_assessed}: Low ${result.low} | Medium ${result.medium} | High ${result.high} | Critical ${result.critical}. ${result.model_training_data}`)
      window.location.reload()
    } finally { setAssessing(false) }
  }

  return (
    <section>
      <p className="eyebrow">Discovery inventory</p>
      <h1>API Inventory</h1>
      <div className="actions">
        <button className="submit" onClick={classify} disabled={running}>{running ? 'Classifying...' : 'Run lifecycle classification'}</button>
        <button className="submit" onClick={assessRisk} disabled={assessing}>{assessing ? 'Assessing risk...' : 'Run risk assessment'}</button>
      </div>
      {summary && <p>{summary}</p>}
      {riskSummary && <p>{riskSummary}</p>}
      {loading && <p>Loading inventory...</p>}
      {error && <p className="error" role="alert">Unable to load API inventory: {error}</p>}
      {!loading && !error && (
        <div className="table-wrap">
          <table>
            <thead><tr><th>Service</th><th>Method</th><th>Endpoint</th><th>Version</th><th>Sources</th><th>Lifecycle / reason</th><th>Risk / findings</th></tr></thead>
            <tbody>
              {apis.length === 0 ? <tr><td colSpan={7} className="empty">No API inventory records yet.</td></tr> : apis.map((api) => (
                <tr key={api.id}>
                  <td><strong>{api.service_name}</strong><br /><small>{api.host}</small></td>
                  <td><code>{api.http_method}</code></td><td><code>{api.endpoint_path}</code></td><td>{api.version}</td><td>{api.sources.join(', ')}</td>
                  <td><span className={`state ${api.lifecycle_state.toLowerCase()}`}>{api.lifecycle_state}</span><br /><small>{api.classification_reason ?? 'Not classified yet'}</small></td>
                  <td>{api.risk_score === null ? <small>Not assessed yet</small> : <><span className={`state risk-${api.risk_level?.toLowerCase()}`}>{api.risk_level} {api.risk_score.toFixed(0)}/100</span><br /><small>{api.risk_findings.slice(0, 2).join(' ')}</small></>}{api.threat_finding_count > 0 && <><br /><small className="threat-count">Threat intelligence findings: {api.threat_finding_count}</small></>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
