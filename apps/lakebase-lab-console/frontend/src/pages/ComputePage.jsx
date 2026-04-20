import { useState, useEffect } from 'react'
import { api } from '../api'

export default function ComputePage() {
  const [branches, setBranches] = useState([])
  const [selectedBranch, setSelectedBranch] = useState('production')
  const [endpoints, setEndpoints] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [editForm, setEditForm] = useState(null)
  const [updating, setUpdating] = useState(false)

  useEffect(() => {
    api.listBranches().then(setBranches).catch(() => {})
  }, [])

  useEffect(() => {
    if (!selectedBranch) return
    setLoading(true)
    api.listEndpoints(selectedBranch)
      .then(setEndpoints)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [selectedBranch])

  const handleUpdate = async (e) => {
    e.preventDefault()
    if (!editForm) return
    setUpdating(true)
    try {
      const epId = editForm.name.split('/').pop()
      await api.updateCompute(selectedBranch, epId, {
        min_cu: editForm.min_cu,
        max_cu: editForm.max_cu,
      })
      setEditForm(null)
      api.listEndpoints(selectedBranch).then(setEndpoints)
    } catch (err) {
      setError(err.message)
    }
    setUpdating(false)
  }

  return (
    <div>
      <div className="page-header">
        <h2>Autoscaling & Compute</h2>
        <p>
          View and adjust compute endpoints. Lakebase autoscales between min and max CU
          based on workload demand. Scale-to-zero suspends compute after inactivity.
        </p>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--danger)' }}>
          <p style={{ color: 'var(--danger)' }}>{error}</p>
          <button className="btn btn-sm btn-secondary" onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      <div className="card">
        <div className="card-header">
          <h3>Compute Endpoints</h3>
          <select
            value={selectedBranch}
            onChange={(e) => setSelectedBranch(e.target.value)}
            style={{ padding: '6px 12px', background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 6, color: 'var(--text-primary)', fontSize: 13 }}
          >
            {branches.map((b) => (
              <option key={b.branch_id} value={b.branch_id}>{b.branch_id}</option>
            ))}
          </select>
        </div>

        {loading ? (
          <p style={{ color: 'var(--text-secondary)' }}>Loading endpoints...</p>
        ) : endpoints.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">⚡</div>
            <p>No endpoints found for this branch.</p>
          </div>
        ) : (
          endpoints.map((ep) => (
            <div key={ep.name} style={{ padding: 16, background: 'var(--bg-primary)', borderRadius: 'var(--radius)', marginBottom: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <div>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{ep.name.split('/').pop()}</span>
                  <span className={`badge ${ep.state?.includes('ACTIVE') ? 'badge-success' : 'badge-warning'}`} style={{ marginLeft: 8 }}>
                    {ep.state || 'unknown'}
                  </span>
                </div>
                <button className="btn btn-secondary btn-sm" onClick={() => setEditForm({ ...ep })}>
                  Edit Scaling
                </button>
              </div>

              <div className="metrics-row">
                <div className="metric-card">
                  <div className="metric-value">{ep.min_cu ?? '--'}</div>
                  <div className="metric-label">Min CU</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value">{ep.max_cu ?? '--'}</div>
                  <div className="metric-label">Max CU</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value">{ep.min_cu != null ? `${(ep.min_cu * 2).toFixed(0)}-${(ep.max_cu * 2).toFixed(0)}` : '--'}</div>
                  <div className="metric-label">RAM (GB)</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value">{ep.endpoint_type?.replace('ENDPOINT_TYPE_', '') || '--'}</div>
                  <div className="metric-label">Type</div>
                </div>
              </div>

              {ep.host && (
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                  Host: {ep.host}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {editForm && (
        <div className="card">
          <h3 style={{ marginBottom: 16 }}>Update Autoscaling Limits</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginBottom: 16 }}>
            Autoscaling range: 0.5-32 CU. The spread (max - min) cannot exceed 8 CU.
            Each CU provides ~2 GB RAM.
          </p>
          <form onSubmit={handleUpdate}>
            <div className="form-row">
              <div className="form-group">
                <label>Min CU</label>
                <input
                  type="number"
                  step="0.5"
                  min="0.5"
                  max="32"
                  value={editForm.min_cu}
                  onChange={(e) => setEditForm({ ...editForm, min_cu: parseFloat(e.target.value) })}
                />
              </div>
              <div className="form-group">
                <label>Max CU</label>
                <input
                  type="number"
                  step="0.5"
                  min="0.5"
                  max="32"
                  value={editForm.max_cu}
                  onChange={(e) => setEditForm({ ...editForm, max_cu: parseFloat(e.target.value) })}
                />
              </div>
            </div>
            {editForm.max_cu - editForm.min_cu > 8 && (
              <p style={{ color: 'var(--danger)', fontSize: 13, marginBottom: 8 }}>
                Spread is {editForm.max_cu - editForm.min_cu} CU (max allowed: 8 CU)
              </p>
            )}
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn-primary" disabled={updating || editForm.max_cu - editForm.min_cu > 8}>
                {updating ? 'Updating...' : 'Apply Changes'}
              </button>
              <button type="button" className="btn btn-secondary" onClick={() => setEditForm(null)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      <div className="card">
        <h3 style={{ marginBottom: 8 }}>Compute Sizing Reference</h3>
        <table className="data-table">
          <thead>
            <tr><th>CU</th><th>RAM</th><th>Max Connections</th><th>Use Case</th></tr>
          </thead>
          <tbody>
            <tr><td>0.5</td><td>~1 GB</td><td>104</td><td>Dev/test, low traffic</td></tr>
            <tr><td>4</td><td>~8 GB</td><td>839</td><td>Small production apps</td></tr>
            <tr><td>8</td><td>~16 GB</td><td>1,678</td><td>Medium production</td></tr>
            <tr><td>16</td><td>~32 GB</td><td>3,357</td><td>High-throughput apps</td></tr>
            <tr><td>32</td><td>~64 GB</td><td>4,000</td><td>Maximum autoscale</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}
