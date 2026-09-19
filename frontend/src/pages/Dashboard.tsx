import type { ApiInventoryItem } from '../types'

interface DashboardProps { health: string; apis: ApiInventoryItem[]; error: string | null }

export function Dashboard({ health, apis, error }: DashboardProps) {
  const lifecycle = (state: string) => apis.filter((api) => api.lifecycle_state === state).length
  const highRisk = apis.filter((api) => api.risk_level === 'HIGH' || api.risk_level === 'CRITICAL').length
  const assessed = apis.filter((api) => api.risk_score !== null).length
  const threats = apis.reduce((total, api) => total + api.threat_finding_count, 0)
  const simulations = apis.reduce((total, api) => total + api.simulation_finding_count, 0)
  return <section>
    <p className="eyebrow">Overview</p><h1>Dashboard</h1>
    {error && <p className="error" role="alert">Unable to reach the backend: {error}</p>}
    <div className="cards">
      <article className="card"><span>Backend status</span><strong className={health === 'healthy' ? 'healthy' : ''}>{health}</strong></article>
      <article className="card"><span>Inventory records</span><strong>{apis.length}</strong></article>
      <article className="card"><span>Zombie APIs</span><strong>{lifecycle('ZOMBIE')}</strong></article>
      <article className="card"><span>High / critical risk</span><strong>{highRisk}</strong></article>
      <article className="card"><span>Risk assessed</span><strong>{assessed}/{apis.length}</strong></article>
      <article className="card"><span>Threat / simulation findings</span><strong>{threats} / {simulations}</strong></article>
    </div>
    <h2>Lifecycle distribution</h2><div className="cards">{['ACTIVE', 'DEPRECATED', 'ZOMBIE', 'DECOMMISSIONED'].map((state) => <article className="card" key={state}><span>{state}</span><strong>{lifecycle(state)}</strong></article>)}</div>
  </section>
}
