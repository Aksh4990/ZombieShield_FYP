interface DashboardProps {
  health: string
  inventoryCount: number
  error: string | null
}

export function Dashboard({ health, inventoryCount, error }: DashboardProps) {
  return (
    <section>
      <p className="eyebrow">Overview</p>
      <h1>Dashboard</h1>
      {error && <p className="error" role="alert">Unable to reach the backend: {error}</p>}
      <div className="cards">
        <article className="card"><span>Backend status</span><strong className={health === 'healthy' ? 'healthy' : ''}>{health}</strong></article>
        <article className="card"><span>Inventory records</span><strong>{inventoryCount}</strong></article>
      </div>
    </section>
  )
}
