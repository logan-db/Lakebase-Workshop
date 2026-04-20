import { useState, useEffect } from 'react'
import { api } from '../api'

function cleanState(raw) {
  if (!raw) return 'unknown'
  const dot = raw.lastIndexOf('.')
  return dot >= 0 ? raw.slice(dot + 1) : raw
}

export default function Dashboard({ onNavigate }) {
  const [health, setHealth] = useState(null)
  const [config, setConfig] = useState(null)
  const [dbStatus, setDbStatus] = useState(null)
  const [stats, setStats] = useState({})
  const [branches, setBranches] = useState([])
  const [endpoints, setEndpoints] = useState([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    Promise.allSettled([
      api.health().then(setHealth),
      api.config().then(setConfig),
      api.dbtest().then(setDbStatus).catch((e) => setDbStatus({ db_connected: false, error: e.message })),
      api.tableStats().then(setStats).catch(() => setStats({})),
      api.listBranches().then(setBranches).catch(() => setBranches([])),
      api.listEndpoints('production').then(setEndpoints).catch(() => setEndpoints([])),
    ]).finally(() => setLoading(false))
  }

  useEffect(load, [])

  const ep = endpoints[0] || {}
  const connected = dbStatus?.db_connected === true
  const totalRows = Object.values(stats).reduce((a, b) => a + (b > 0 ? b : 0), 0)

  return (
    <div>
      <div className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h2>Dashboard</h2>
            <p>Lakebase Autoscaling project overview and health</p>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={load} disabled={loading}>
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Status Banner */}
      <div className={`status-banner ${connected ? 'status-healthy' : 'status-error'}`}>
        <div className="status-banner-left">
          <span className={`pulse-dot ${connected ? 'pulse-green' : 'pulse-red'}`} />
          <div>
            <div className="status-banner-title">
              {connected ? 'Lakebase Connected' : 'Lakebase Disconnected'}
            </div>
            <div className="status-banner-detail">
              {config?.project_id || 'No project configured'}
              {ep.state && <> &middot; Compute: {cleanState(ep.state)}</>}
            </div>
            {!connected && dbStatus?.error && (
              <div style={{ fontSize: 11, color: 'var(--danger)', marginTop: 4, maxWidth: 500, wordBreak: 'break-word' }}>
                {dbStatus.error}
              </div>
            )}
          </div>
        </div>
        <div className="status-banner-right">
          <span className="badge badge-info">{config?.branch_id || 'production'}</span>
          <span className="badge badge-success">{config?.schema || 'demo'}</span>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="metrics-row" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
        <div className="metric-card">
          <div className="metric-icon">&#9889;</div>
          <div className="metric-value">{ep.min_cu ?? '--'}-{ep.max_cu ?? '--'}</div>
          <div className="metric-label">Compute (CU)</div>
        </div>
        <div className="metric-card">
          <div className="metric-icon">&#9875;</div>
          <div className="metric-value">{branches.length}</div>
          <div className="metric-label">Branches</div>
        </div>
        <div className="metric-card">
          <div className="metric-icon">&#128451;</div>
          <div className="metric-value">{Object.keys(stats).length}</div>
          <div className="metric-label">Tables</div>
        </div>
        <div className="metric-card">
          <div className="metric-icon">&#128200;</div>
          <div className="metric-value">{totalRows.toLocaleString()}</div>
          <div className="metric-label">Total Rows</div>
        </div>
      </div>

      {/* Table Stats + Endpoint */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
        <div className="card">
          <div className="card-header">
            <h3>Table Overview</h3>
          </div>
          {Object.keys(stats).length === 0 ? (
            <div className="empty-state" style={{ padding: 20 }}>
              <p style={{ fontSize: 12 }}>{connected ? 'Loading table stats...' : 'Connect to Lakebase to view tables'}</p>
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr><th>Table</th><th style={{ textAlign: 'right' }}>Rows</th></tr>
              </thead>
              <tbody>
                {Object.entries(stats).map(([name, count]) => (
                  <tr key={name}>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>demo.{name}</td>
                    <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                      {count >= 0 ? count.toLocaleString() : <span className="badge badge-danger">error</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="card">
          <div className="card-header">
            <h3>Endpoint Details</h3>
          </div>
          {ep.name ? (
            <div style={{ fontSize: 13 }}>
              <div className="detail-row">
                <span className="detail-label">Endpoint</span>
                <span className="detail-value">{ep.name?.split('/').pop()}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">State</span>
                <span className={`badge ${ep.state?.includes('ACTIVE') ? 'badge-success' : 'badge-warning'}`}>
                  {cleanState(ep.state)}
                </span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Type</span>
                <span className="detail-value">{ep.endpoint_type?.replace(/^.*\./, '') || '--'}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Autoscaling</span>
                <span className="detail-value">{ep.min_cu ?? '--'} - {ep.max_cu ?? '--'} CU</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Memory</span>
                <span className="detail-value">{ep.min_cu != null ? `${(ep.min_cu * 2).toFixed(0)}-${(ep.max_cu * 2).toFixed(0)} GB` : '--'}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Host</span>
                <span className="detail-value" style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>{ep.host || '--'}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Database</span>
                <span className="detail-value">{dbStatus?.info?.db || config?.database || 'databricks_postgres'}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">PG Version</span>
                <span className="detail-value" style={{ fontSize: 12 }}>{dbStatus?.info?.version?.split('(')[0]?.trim() || '--'}</span>
              </div>
            </div>
          ) : (
            <div className="empty-state" style={{ padding: 20 }}>
              <p>No endpoint data available</p>
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <div className="card-header">
          <h3>Quick Actions</h3>
        </div>
        <div className="quick-actions-grid">
          <button className="quick-action-card" onClick={() => onNavigate('autoscale')}>
            <div className="qa-icon">&#128200;</div>
            <div className="qa-title">Autoscale Demo</div>
            <div className="qa-desc">Spike traffic and watch compute scale in real time</div>
          </button>
          <button className="quick-action-card" onClick={() => onNavigate('branches')}>
            <div className="qa-icon">&#9875;</div>
            <div className="qa-title">Branch Manager</div>
            <div className="qa-desc">Create, review, and delete database branches</div>
          </button>
          <button className="quick-action-card" onClick={() => onNavigate('data')}>
            <div className="qa-icon">&#128451;</div>
            <div className="qa-title">Data Ops</div>
            <div className="qa-desc">CRUD operations, JSONB queries, audit log</div>
          </button>
          <button className="quick-action-card" onClick={() => onNavigate('agent')}>
            <div className="qa-icon">&#129302;</div>
            <div className="qa-title">Agent Memory</div>
            <div className="qa-desc">Persistent AI agent session and message storage</div>
          </button>
          <button className="quick-action-card" onClick={() => onNavigate('compute')}>
            <div className="qa-icon">&#9889;</div>
            <div className="qa-title">Compute Config</div>
            <div className="qa-desc">Configure compute CU limits and view endpoints</div>
          </button>
          <button className="quick-action-card" onClick={() => onNavigate('sync')}>
            <div className="qa-icon">&#128260;</div>
            <div className="qa-title">Reverse ETL</div>
            <div className="qa-desc">Sync Delta Lake tables into Lakebase</div>
          </button>
          <button className="quick-action-card" onClick={() => onNavigate('api')}>
            <div className="qa-icon">&#128268;</div>
            <div className="qa-title">API Tester</div>
            <div className="qa-desc">Execute raw API calls against Lakebase</div>
          </button>
          <a className="quick-action-card" href="https://docs.databricks.com/aws/en/oltp/projects/" target="_blank" rel="noopener noreferrer">
            <div className="qa-icon">&#128214;</div>
            <div className="qa-title">Lakebase Docs</div>
            <div className="qa-desc">Official Databricks Lakebase documentation</div>
          </a>
        </div>
      </div>
    </div>
  )
}
