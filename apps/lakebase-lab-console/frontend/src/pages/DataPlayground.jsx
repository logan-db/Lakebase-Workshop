import { useState, useEffect } from 'react'
import { api } from '../api'
import { Database, Plus, Trash2, RefreshCw, Check, Table, Clock, AlertCircle } from '../icons'

export default function DataPlayground() {
  const [tab, setTab] = useState('products')
  const [products, setProducts] = useState([])
  const [audit, setAudit] = useState([])
  const [stats, setStats] = useState({})
  const [loading, setLoading] = useState(false)
  const [showAdd, setShowAdd] = useState(false)
  const [form, setForm] = useState({ name: '', price: '', stock_quantity: '', category: 'General', description: '' })
  const [toast, setToast] = useState(null)

  const loadProducts = () => {
    setLoading(true)
    api.listProducts().then(setProducts).finally(() => setLoading(false))
  }
  const loadAudit = () => api.listAudit().then(setAudit)
  const loadStats = () => api.tableStats().then(setStats)

  useEffect(() => {
    loadProducts()
    loadAudit()
    loadStats()
  }, [])

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3000)
  }

  const handleAdd = async (e) => {
    e.preventDefault()
    try {
      await api.createProduct({
        name: form.name,
        description: form.description,
        price: parseFloat(form.price),
        stock_quantity: parseInt(form.stock_quantity) || 0,
        category: form.category,
        tags: [],
      })
      showToast('Product created')
      setForm({ name: '', price: '', stock_quantity: '', category: 'General', description: '' })
      setShowAdd(false)
      loadProducts()
      loadAudit()
      loadStats()
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  const handleDelete = async (id) => {
    try {
      await api.deleteProduct(id)
      showToast('Product deleted')
      loadProducts()
      loadAudit()
      loadStats()
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  return (
    <div>
      <div className="page-header">
        <h2>Data Playground</h2>
        <p>
          Perform CRUD operations on the seeded demo tables. Changes are tracked
          automatically via PostgreSQL triggers in the audit log.
        </p>
      </div>

      <div className="metrics-row">
        {Object.entries(stats).map(([table, count]) => (
          <div className="metric-card" key={table}>
            <div className="metric-icon"><Table size={16} /></div>
            <div className="metric-value">{count >= 0 ? count.toLocaleString() : 'err'}</div>
            <div className="metric-label">{table}</div>
          </div>
        ))}
      </div>

      <div className="tab-group">
        <button className={`tab-btn ${tab === 'products' ? 'active' : ''}`} onClick={() => setTab('products')}>
          Products
        </button>
        <button className={`tab-btn ${tab === 'audit' ? 'active' : ''}`} onClick={() => { setTab('audit'); loadAudit() }}>
          Audit Log
        </button>
      </div>

      {tab === 'products' && (
        <div className="card">
          <div className="card-header">
            <h3><Database size={16} /> Products ({products.length})</h3>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn-primary btn-sm" onClick={() => setShowAdd(!showAdd)}>
                <Plus size={14} /> Add Product
              </button>
              <button className="btn btn-secondary btn-sm btn-icon" onClick={loadProducts}>
                <RefreshCw size={14} />
              </button>
            </div>
          </div>

          {showAdd && (
            <form onSubmit={handleAdd} style={{ marginBottom: 16, padding: 18, background: 'var(--bg-secondary)', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
              <div className="form-row">
                <div className="form-group">
                  <label>Name</label>
                  <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
                </div>
                <div className="form-group">
                  <label>Category</label>
                  <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
                    <option>Electronics</option><option>Books</option><option>Accessories</option>
                    <option>Office</option><option>General</option>
                  </select>
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Price</label>
                  <input type="number" step="0.01" min="0" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} required />
                </div>
                <div className="form-group">
                  <label>Stock Quantity</label>
                  <input type="number" min="0" value={form.stock_quantity} onChange={(e) => setForm({ ...form, stock_quantity: e.target.value })} />
                </div>
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn btn-primary">
                  <Check size={14} /> Save Product
                </button>
                <button type="button" className="btn btn-secondary" onClick={() => setShowAdd(false)}>Cancel</button>
              </div>
            </form>
          )}

          {loading ? (
            <div className="empty-state" style={{ padding: 20 }}><p>Loading...</p></div>
          ) : products.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon"><Database size={36} /></div>
              <p>No products found</p>
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th><th>Name</th><th>Price</th><th>Stock</th><th>Category</th><th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {products.map((p) => (
                  <tr key={p.product_id}>
                    <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>{p.product_id}</td>
                    <td style={{ fontWeight: 600 }}>{p.name}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>${parseFloat(p.price).toFixed(2)}</td>
                    <td>
                      <span className={`badge ${p.stock_quantity > 50 ? 'badge-success' : p.stock_quantity > 0 ? 'badge-warning' : 'badge-danger'}`}>
                        {p.stock_quantity}
                      </span>
                    </td>
                    <td><span className="badge badge-purple">{p.category}</span></td>
                    <td style={{ textAlign: 'right' }}>
                      <button className="btn btn-danger btn-xs" onClick={() => handleDelete(p.product_id)}>
                        <Trash2 size={12} /> Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {tab === 'audit' && (
        <div className="card">
          <div className="card-header">
            <h3><Clock size={16} /> Audit Log (last 50)</h3>
            <button className="btn btn-secondary btn-sm btn-icon" onClick={loadAudit}>
              <RefreshCw size={14} />
            </button>
          </div>
          {audit.length === 0 ? (
            <div className="empty-state" style={{ padding: 20 }}><p>No audit entries yet</p></div>
          ) : (
            <table className="data-table">
              <thead>
                <tr><th>ID</th><th>Table</th><th>Operation</th><th>Record ID</th><th>Time</th></tr>
              </thead>
              <tbody>
                {audit.map((a) => (
                  <tr key={a.audit_id}>
                    <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>{a.audit_id}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{a.table_name}</td>
                    <td>
                      <span className={`badge ${a.operation === 'INSERT' ? 'badge-success' : a.operation === 'DELETE' ? 'badge-danger' : 'badge-warning'}`}>
                        {a.operation}
                      </span>
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{a.record_id}</td>
                    <td style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{a.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {toast && (
        <div className={`toast toast-${toast.type}`}>
          {toast.type === 'success' ? <Check size={16} /> : <AlertCircle size={16} />}
          {toast.msg}
        </div>
      )}
    </div>
  )
}
