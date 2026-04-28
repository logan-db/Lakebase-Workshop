import { useState } from 'react'
import { Terminal, Play, Clock, AlertCircle, Check } from '../icons'

const PRESETS = [
  { label: 'Health Check', method: 'GET', path: '/api/health' },
  { label: 'DB Test', method: 'GET', path: '/api/dbtest' },
  { label: 'App Config', method: 'GET', path: '/api/config' },
  { label: 'List Branches', method: 'GET', path: '/api/branches' },
  { label: 'List Products', method: 'GET', path: '/api/data/products' },
  { label: 'Table Stats', method: 'GET', path: '/api/data/stats' },
  { label: 'Audit Log', method: 'GET', path: '/api/data/audit' },
  { label: 'Agent Sessions', method: 'GET', path: '/api/agent/sessions' },
  { label: 'Create Event', method: 'POST', path: '/api/data/events', body: { event_type: 'test', source: 'api-tester', payload: { hello: 'world' } } },
  { label: 'Create Product', method: 'POST', path: '/api/data/products', body: { name: 'Test Product', price: 9.99, category: 'General', stock_quantity: 10 } },
]

export default function ApiTester() {
  const [method, setMethod] = useState('GET')
  const [path, setPath] = useState('/api/health')
  const [body, setBody] = useState('')
  const [response, setResponse] = useState(null)
  const [error, setError] = useState(false)
  const [loading, setLoading] = useState(false)
  const [elapsed, setElapsed] = useState(null)

  const send = async () => {
    setLoading(true)
    setResponse(null)
    setError(false)
    const start = performance.now()
    try {
      const opts = { method, headers: { 'Content-Type': 'application/json' } }
      if (method !== 'GET' && body.trim()) {
        opts.body = body
      }
      const res = await fetch(path, opts)
      const data = await res.json()
      setElapsed(Math.round(performance.now() - start))
      if (!res.ok) {
        setError(true)
        setResponse(JSON.stringify({ status: res.status, ...data }, null, 2))
      } else {
        setResponse(JSON.stringify(data, null, 2))
      }
    } catch (e) {
      setElapsed(Math.round(performance.now() - start))
      setError(true)
      setResponse(e.message)
    }
    setLoading(false)
  }

  const applyPreset = (preset) => {
    setMethod(preset.method)
    setPath(preset.path)
    setBody(preset.body ? JSON.stringify(preset.body, null, 2) : '')
    setResponse(null)
  }

  return (
    <div>
      <div className="page-header">
        <h2>API Tester</h2>
        <p>
          Exercise the Lab Console's FastAPI routes directly from the browser.
          Useful for debugging and understanding the Lakebase integration.
        </p>
      </div>

      <div className="card">
        <div className="card-header">
          <h3><Terminal size={16} /> Presets</h3>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {PRESETS.map((p) => (
            <button key={p.label} className="btn btn-secondary btn-sm" onClick={() => applyPreset(p)}>
              <span className={`badge ${p.method === 'GET' ? 'badge-success' : 'badge-warning'}`}>{p.method}</span>
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Request</h3>
        </div>
        <div className="form-row">
          <div className="form-group">
            <label>Method</label>
            <select value={method} onChange={(e) => setMethod(e.target.value)}>
              <option>GET</option><option>POST</option><option>PUT</option>
              <option>PATCH</option><option>DELETE</option>
            </select>
          </div>
          <div className="form-group">
            <label>Path</label>
            <input value={path} onChange={(e) => setPath(e.target.value)} placeholder="/api/..." />
          </div>
        </div>
        {method !== 'GET' && (
          <div className="form-group">
            <label>Body (JSON)</label>
            <textarea
              rows={5}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder='{"key": "value"}'
              style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}
            />
          </div>
        )}
        <button className="btn btn-primary" onClick={send} disabled={loading}>
          <Play size={14} />
          {loading ? 'Sending...' : 'Send Request'}
        </button>
      </div>

      {response !== null && (
        <div className="card">
          <div className="card-header">
            <h3>
              {error ? <AlertCircle size={16} style={{ color: 'var(--danger)' }} /> : <Check size={16} style={{ color: 'var(--success)' }} />}
              Response
            </h3>
            {elapsed !== null && (
              <span className="badge badge-info">
                <Clock size={11} /> {elapsed}ms
              </span>
            )}
          </div>
          <div className={`api-response ${error ? 'error' : ''}`}>
            {response}
          </div>
        </div>
      )}
    </div>
  )
}
