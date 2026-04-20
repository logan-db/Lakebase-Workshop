import { useState, useEffect } from 'react'
import { api } from '../api'

export default function BranchManager() {
  const [branches, setBranches] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ branch_id: 'lab-', source_branch: 'production', ttl_hours: 24 })
  const [creating, setCreating] = useState(false)

  const load = () => {
    setLoading(true)
    api.listBranches()
      .then(setBranches)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    setCreating(true)
    try {
      await api.createBranch(form)
      setShowCreate(false)
      setForm({ branch_id: 'lab-', source_branch: 'production', ttl_hours: 24 })
      load()
    } catch (err) {
      setError(err.message)
    }
    setCreating(false)
  }

  const handleDelete = async (id) => {
    if (!confirm(`Delete branch "${id}"? This cannot be undone.`)) return
    try {
      await api.deleteBranch(id)
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h2>Branch Manager</h2>
        <p>
          Create isolated database environments with copy-on-write storage.
          Each branch gets its own compute endpoint and full PostgreSQL instance.
        </p>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--danger)', marginBottom: 16 }}>
          <p style={{ color: 'var(--danger)' }}>{error}</p>
          <button className="btn btn-sm btn-secondary" onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      <div className="card">
        <div className="card-header">
          <h3>Branches ({branches.length})</h3>
          <button className="btn btn-primary btn-sm" onClick={() => setShowCreate(!showCreate)}>
            + New Branch
          </button>
        </div>

        {showCreate && (
          <form onSubmit={handleCreate} style={{ marginBottom: 20, padding: 16, background: 'var(--bg-primary)', borderRadius: 'var(--radius)' }}>
            <div className="form-row">
              <div className="form-group">
                <label>Branch ID (must start with lab-)</label>
                <input
                  value={form.branch_id}
                  onChange={(e) => setForm({ ...form, branch_id: e.target.value })}
                  placeholder="lab-my-feature"
                  pattern="^lab-[a-z0-9-]{1,50}$"
                  required
                />
              </div>
              <div className="form-group">
                <label>Source Branch</label>
                <select value={form.source_branch} onChange={(e) => setForm({ ...form, source_branch: e.target.value })}>
                  {branches.map((b) => (
                    <option key={b.branch_id} value={b.branch_id}>{b.branch_id}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="form-group">
              <label>TTL (hours)</label>
              <input
                type="number"
                value={form.ttl_hours}
                onChange={(e) => setForm({ ...form, ttl_hours: parseInt(e.target.value) || 24 })}
                min={1}
                max={720}
              />
            </div>
            <button className="btn btn-primary" disabled={creating}>
              {creating ? 'Creating...' : 'Create Branch'}
            </button>
          </form>
        )}

        {loading ? (
          <p style={{ color: 'var(--text-secondary)' }}>Loading branches...</p>
        ) : branches.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">⑂</div>
            <p>No branches found. Is LAKEBASE_PROJECT_ID configured?</p>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Branch ID</th>
                <th>State</th>
                <th>Default</th>
                <th>Protected</th>
                <th>Expires</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {branches.map((b) => (
                <tr key={b.branch_id}>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{b.branch_id}</td>
                  <td>
                    <span className={`badge ${b.state?.includes('ACTIVE') ? 'badge-success' : 'badge-warning'}`}>
                      {b.state || 'unknown'}
                    </span>
                  </td>
                  <td>{b.is_default ? 'Yes' : ''}</td>
                  <td>{b.is_protected ? 'Yes' : ''}</td>
                  <td style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                    {b.expire_time && b.expire_time !== 'None' ? b.expire_time : '--'}
                  </td>
                  <td>
                    {b.branch_id.startsWith('lab-') && (
                      <button className="btn btn-danger btn-sm" onClick={() => handleDelete(b.branch_id)}>
                        Delete
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="card">
        <h3 style={{ marginBottom: 8 }}>How Branching Works</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginBottom: 12 }}>
          Lakebase branches use <strong>copy-on-write</strong> storage. Creating a branch is instant
          and doesn't duplicate data. Changes on a branch are isolated until you manually promote them.
        </p>
        <div className="code-block">{`Project
  └── production (default, protected)
        ├── lab-feature-a (TTL: 24h)
        │     └── Compute: 0.5-4 CU
        └── lab-feature-b (TTL: 48h)
              └── Compute: 0.5-4 CU`}</div>
      </div>
    </div>
  )
}
