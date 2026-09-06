import type { ApiInventoryItem } from '../types'
import { runClassification } from '../api'
import { useState } from 'react'

interface ApiInventoryProps {
  apis: ApiInventoryItem[]
  loading: boolean
  error: string | null
}

export function ApiInventory({ apis, loading, error }: ApiInventoryProps) {
  const [summary, setSummary] = useState<string | null>(null)
  const [running, setRunning] = useState(false)
  const classify = async () => { setRunning(true); try { const r = await runClassification(); setSummary(`Active ${r.active} · Deprecated ${r.deprecated} · Zombie ${r.zombie} · Decommissioned ${r.decommissioned}`); window.location.reload() } finally { setRunning(false) } }
  return (
    <section>
      <p className="eyebrow">Discovery inventory</p>
      <h1>API Inventory</h1><button className="submit" onClick={classify} disabled={running}>{running ? 'Classifying…' : 'Run lifecycle classification'}</button>{summary && <p>{summary}</p>}
      {loading && <p>Loading inventory…</p>}
      {error && <p className="error" role="alert">Unable to load API inventory: {error}</p>}
      {!loading && !error && (
        <div className="table-wrap">
          <table>
            <thead><tr><th>Service</th><th>Method</th><th>Endpoint</th><th>Version</th><th>Sources</th><th>Lifecycle / reason</th></tr></thead>
            <tbody>
              {apis.length === 0 ? <tr><td colSpan={6} className="empty">No API inventory records yet.</td></tr> : apis.map((api) => (
                <tr key={api.id}><td><strong>{api.service_name}</strong><br /><small>{api.host}</small></td><td><code>{api.http_method}</code></td><td><code>{api.endpoint_path}</code></td><td>{api.version}</td><td>{api.sources.join(', ')}</td><td><span className={`state ${api.lifecycle_state.toLowerCase()}`}>{api.lifecycle_state}</span><br /><small>{api.classification_reason ?? 'Not classified yet'}</small></td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
