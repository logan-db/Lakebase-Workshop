import { useState, useEffect, useRef } from 'react'
import { api } from '../api'
import { Play, Square, Activity, Clock, AlertCircle, Trash2, X } from '../icons'

export default function LoadTestPage() {
  const [form, setForm] = useState({ concurrency: 10, duration_seconds: 60, write_ratio: 0.3 })
  const [testId, setTestId] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [history, setHistory] = useState([])
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState(null)
  const pollRef = useRef(null)

  const startTest = async () => {
    setStarting(true)
    setError(null)
    setHistory([])
    try {
      const res = await api.startLoadTest(form)
      setTestId(res.test_id)
      setMetrics(res)
    } catch (e) {
      setError(e.message)
    }
    setStarting(false)
  }

  const stopTest = async () => {
    if (testId) {
      try { await api.stopLoadTest(testId) } catch {}
    }
  }

  useEffect(() => {
    if (!testId) return
    pollRef.current = setInterval(async () => {
      try {
        const s = await api.loadTestStatus(testId)
        setMetrics(s)
        setHistory((h) => [...h.slice(-59), { qps: s.qps, avg: s.avg_latency_ms, p95: s.p95_latency_ms }])
        if (!s.running) {
          clearInterval(pollRef.current)
        }
      } catch {}
    }, 1000)
    return () => clearInterval(pollRef.current)
  }, [testId])

  const maxQps = Math.max(...history.map((h) => h.qps), 1)
  const maxLat = Math.max(...history.map((h) => h.p95), 1)

  return (
    <div>
      <div className="page-header">
        <h2>Load Test</h2>
        <p>
          Generate synthetic traffic against Lakebase to observe autoscaling behavior.
          Watch QPS and latency in real time.
        </p>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'rgba(239, 68, 68, 0.3)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <AlertCircle size={18} style={{ color: 'var(--danger)', flexShrink: 0 }} />
            <p style={{ color: 'var(--danger)', flex: 1 }}>{error}</p>
            <button className="btn btn-sm btn-secondary btn-icon" onClick={() => setError(null)}>
              <X size={14} />
            </button>
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-header">
          <h3>Test Configuration</h3>
        </div>
        <div className="form-row">
          <div className="form-group">
            <label>Concurrent Workers</label>
            <input
              type="number" min={1} max={100}
              value={form.concurrency}
              onChange={(e) => setForm({ ...form, concurrency: parseInt(e.target.value) || 10 })}
              disabled={metrics?.running}
            />
          </div>
          <div className="form-group">
            <label>Duration (seconds)</label>
            <input
              type="number" min={5} max={600}
              value={form.duration_seconds}
              onChange={(e) => setForm({ ...form, duration_seconds: parseInt(e.target.value) || 60 })}
              disabled={metrics?.running}
            />
          </div>
        </div>
        <div className="form-group">
          <label>Write Ratio ({Math.round(form.write_ratio * 100)}% writes / {Math.round((1 - form.write_ratio) * 100)}% reads)</label>
          <input
            type="range" min={0} max={1} step={0.1}
            value={form.write_ratio}
            onChange={(e) => setForm({ ...form, write_ratio: parseFloat(e.target.value) })}
            disabled={metrics?.running}
          />
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {!metrics?.running ? (
            <button className="btn btn-primary" onClick={startTest} disabled={starting}>
              <Play size={14} />
              {starting ? 'Starting...' : 'Start Load Test'}
            </button>
          ) : (
            <button className="btn btn-danger" onClick={stopTest}>
              <Square size={14} /> Stop Test
            </button>
          )}
          <button className="btn btn-secondary" onClick={() => api.clearLoadtestEvents()}>
            <Trash2 size={14} /> Clear Test Events
          </button>
        </div>
      </div>

      {metrics && (
        <>
          <div className="metrics-row">
            <div className="metric-card">
              <div className="metric-value">{metrics.qps}</div>
              <div className="metric-label">QPS</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{metrics.total_queries.toLocaleString()}</div>
              <div className="metric-label">Total Queries</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{metrics.avg_latency_ms}</div>
              <div className="metric-label">Avg Latency (ms)</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{metrics.p95_latency_ms}</div>
              <div className="metric-label">P95 Latency (ms)</div>
            </div>
            <div className="metric-card">
              <div className="metric-value" style={{ color: metrics.total_errors > 0 ? 'var(--danger)' : 'var(--success)' }}>
                {metrics.total_errors}
              </div>
              <div className="metric-label">Errors</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{metrics.elapsed_seconds}s</div>
              <div className="metric-label">Elapsed</div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h3><Activity size={16} /> QPS Over Time</h3>
            </div>
            <div className="chart-area">
              {history.length === 0 ? (
                <div className="empty-state"><p>Waiting for data...</p></div>
              ) : (
                history.map((h, i) => (
                  <div className="chart-bar-row" key={i}>
                    <span className="chart-bar-label">{h.qps}</span>
                    <div className="chart-bar" style={{ width: `${(h.qps / maxQps) * 100}%` }} />
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h3><Clock size={16} /> P95 Latency Over Time (ms)</h3>
            </div>
            <div className="chart-area">
              {history.length === 0 ? (
                <div className="empty-state"><p>Waiting for data...</p></div>
              ) : (
                history.map((h, i) => (
                  <div className="chart-bar-row" key={i}>
                    <span className="chart-bar-label">{h.p95.toFixed(0)}</span>
                    <div className="chart-bar latency" style={{ width: `${(h.p95 / maxLat) * 100}%` }} />
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
