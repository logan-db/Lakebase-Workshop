import { useState, useEffect } from 'react'
import { api } from '../api'

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
            <div className="metric-value">{count >= 0 ? count.toLocaleString() : 'err'}</div>
            <div className="metric-label">{table}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {['products', 'audit'].map((t) => (
          <button
            key={t}
            className={`btn ${tab === t ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => { setTab(t); t === 'audit' && loadAudit() }}
          >
            {t === 'products' ? 'Products' : 'Audit Log'}
          </button>
        ))}
      </div>

      {tab === 'products' && (
        <div className="card">
          <div className="card-header">
            <h3>Products ({products.length})</h3>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn-primary btn-sm" onClick={() => setShowAdd(!showAdd)}>+ Add Product</button>
              <button className="btn btn-secondary btn-sm" onClick={loadProducts}>Refresh</button>
            </div>
          </div>

          {showAdd && (
            <form onSubmit={handleAdd} style={{ marginBottom: 16, padding: 16, background: 'var(--bg-primary)', borderRadius: 'var(--radius)' }}>
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
              <button className="btn btn-primary">Save Product</button>
            </form>
          )}

          {loading ? <p style={{ color: 'var(--text-secondary)' }}>Loading...</p> : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th><th>Name</th><th>Price</th><th>Stock</th><th>Category</th><th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {products.map((p) => (
                  <tr key={p.product_id}>
                    <td>{p.product_id}</td>
                    <td style={{ fontWeight: 500 }}>{p.name}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>${parseFloat(p.price).toFixed(2)}</td>
                    <td>
                      <span className={`badge ${p.stock_quantity > 50 ? 'badge-success' : p.stock_quantity > 0 ? 'badge-warning' : 'badge-danger'}`}>
                        {p.stock_quantity}
                      </span>
                    </td>
                    <td>{p.category}</td>
                    <td>
                      <button className="btn btn-danger btn-sm" onClick={() => handleDelete(p.product_id)}>Delete</button>
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
            <h3>Audit Log (last 50)</h3>
            <button className="btn btn-secondary btn-sm" onClick={loadAudit}>Refresh</button>
          </div>
          <table className="data-table">
            <thead>
              <tr><th>ID</th><th>Table</th><th>Operation</th><th>Record ID</th><th>Time</th></tr>
            </thead>
            <tbody>
              {audit.map((a) => (
                <tr key={a.audit_id}>
                  <td>{a.audit_id}</td>
                  <td>{a.table_name}</td>
                  <td>
                    <span className={`badge ${a.operation === 'INSERT' ? 'badge-success' : a.operation === 'DELETE' ? 'badge-danger' : 'badge-warning'}`}>
                      {a.operation}
                    </span>
                  </td>
                  <td>{a.record_id}</td>
                  <td style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{a.created_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {toast && <div className={`toast toast-${toast.type}`}>{toast.msg}</div>}
    </div>
  )
}
