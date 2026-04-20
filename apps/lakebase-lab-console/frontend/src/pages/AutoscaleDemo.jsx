import { useState, useEffect, useRef, useCallback } from 'react'
import { api } from '../api'

function cleanState(raw) {
  if (!raw) return 'unknown'
  const dot = raw.lastIndexOf('.')
  return dot >= 0 ? raw.slice(dot + 1) : raw
}

const PRESETS = [
  { label: 'Light', icon: '\u2600', concurrency: 3, duration_seconds: 30, write_ratio: 0.2, desc: '3 workers, 30s' },
  { label: 'Medium', icon: '\uD83D\uDD25', concurrency: 10, duration_seconds: 60, write_ratio: 0.4, desc: '10 workers, 60s' },
  { label: 'Heavy', icon: '\u26A1', concurrency: 25, duration_seconds: 90, write_ratio: 0.5, desc: '25 workers, 90s' },
  { label: 'Extreme', icon: '\uD83D\uDCA5', concurrency: 50, duration_seconds: 120, write_ratio: 0.6, desc: '50 workers, 120s' },
]

export default function AutoscaleDemo() {
  const [form, setForm] = useState({ concurrency: 10, duration_seconds: 60, write_ratio: 0.4 })
  const [testId, setTestId] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [history, setHistory] = useState([])
  const [computeHistory, setComputeHistory] = useState([])
  const [endpoints, setEndpoints] = useState([])
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState(null)
  const [showCustom, setShowCustom] = useState(false)
  const pollRef = useRef(null)
  const computePollRef = useRef(null)
  const isRunning = metrics?.running === true

  const loadCompute = useCallback(async () => {
    try {
      const eps = await api.listEndpoints('production')
      setEndpoints(eps)
      return eps
    } catch { return [] }
  }, [])

  useEffect(() => { loadCompute() }, [loadCompute])

  const startTest = async (preset) => {
    const config = preset || form
    setStarting(true)
    setError(null)
    setHistory([])
    setComputeHistory([])
    try {
      const res = await api.startLoadTest(config)
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
        setHistory((h) => [...h.slice(-89), {
          t: Math.round(s.elapsed_seconds),
          qps: s.qps,
          avg: s.avg_latency_ms,
          p95: s.p95_latency_ms,
          errors: s.total_errors,
        }])
        if (!s.running) clearInterval(pollRef.current)
      } catch {}
    }, 1000)

    computePollRef.current = setInterval(async () => {
      try {
        const eps = await api.listEndpoints('production')
        setEndpoints(eps)
        const ep = eps[0]
        if (ep) {
          setComputeHistory((h) => [...h.slice(-29), {
            t: Date.now(),
            state: cleanState(ep.state),
            min_cu: ep.min_cu,
            max_cu: ep.max_cu,
          }])
        }
      } catch {}
    }, 5000)

    return () => {
      clearInterval(pollRef.current)
      clearInterval(computePollRef.current)
    }
  }, [testId])

  const ep = endpoints[0] || {}
  const maxQps = Math.max(...history.map((h) => h.qps), 1)
  const maxLat = Math.max(...history.map((h) => h.p95), 1)
  const barHeight = history.length > 60 ? 6 : history.length > 30 ? 10 : 16

  return (
    <div>
      <div className="page-header">
        <h2>Autoscale Demo</h2>
        <p>
          Send traffic spikes to Lakebase and watch compute respond in real time.
          The autoscaler adjusts CU allocation based on workload demand.
        </p>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--danger)' }}>
          <p style={{ color: 'var(--danger)' }}>{error}</p>
          <button className="btn btn-sm btn-secondary" onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      {/* Compute Status Bar */}
      <div className="card">
        <div className="card-header">
          <h3>Compute Status</h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className={`badge ${ep.state?.includes('ACTIVE') ? 'badge-success' : 'badge-warning'}`}>
              {cleanState(ep.state)}
            </span>
            {isRunning && <span className="badge badge-info" style={{ animation: 'pulse 2s infinite' }}>MONITORING</span>}
          </div>
        </div>
        <div className="metrics-row" style={{ gridTemplateColumns: 'repeat(5, 1fr)', marginBottom: 0 }}>
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
            <div className="metric-value">{ep.endpoint_type?.replace(/^.*\./, '') || '--'}</div>
            <div className="metric-label">Type</div>
          </div>
          <div className="metric-card">
            <div className="metric-value" style={{ fontSize: 14, fontFamily: 'var(--font-mono)' }}>{ep.host?.split('.')[0] || '--'}</div>
            <div className="metric-label">Host</div>
          </div>
        </div>
      </div>

      {/* Spike Controls */}
      <div className="card">
        <div className="card-header">
          <h3>{isRunning ? 'Spike In Progress' : 'Send a Traffic Spike'}</h3>
          {isRunning && (
            <button className="btn btn-danger btn-sm" onClick={stopTest}>Stop</button>
          )}
        </div>

        {!isRunning && (
          <>
            <div className="spike-presets">
              {PRESETS.map((p) => (
                <button
                  key={p.label}
                  className="spike-preset-btn"
                  onClick={() => startTest(p)}
                  disabled={starting}
                >
                  <span className="spike-preset-icon">{p.icon}</span>
                  <span className="spike-preset-label">{p.label}</span>
                  <span className="spike-preset-desc">{p.desc}</span>
                </button>
              ))}
            </div>

            <div style={{ marginTop: 12 }}>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => setShowCustom(!showCustom)}
                style={{ fontSize: 12 }}
              >
                {showCustom ? 'Hide' : 'Show'} Custom Config
              </button>
            </div>

            {showCustom && (
              <div style={{ marginTop: 14, padding: 16, background: 'var(--bg-primary)', borderRadius: 'var(--radius)' }}>
                <div className="form-row">
                  <div className="form-group">
                    <label>Concurrent Workers</label>
                    <input
                      type="number" min={1} max={50}
                      value={form.concurrency}
                      onChange={(e) => setForm({ ...form, concurrency: parseInt(e.target.value) || 5 })}
                    />
                  </div>
                  <div className="form-group">
                    <label>Duration (seconds)</label>
                    <input
                      type="number" min={5} max={300}
                      value={form.duration_seconds}
                      onChange={(e) => setForm({ ...form, duration_seconds: parseInt(e.target.value) || 30 })}
                    />
                  </div>
                </div>
                <div className="form-group">
                  <label>Write Ratio ({Math.round(form.write_ratio * 100)}% writes / {Math.round((1 - form.write_ratio) * 100)}% reads)</label>
                  <input
                    type="range" min={0} max={1} step={0.1}
                    value={form.write_ratio}
                    onChange={(e) => setForm({ ...form, write_ratio: parseFloat(e.target.value) })}
                  />
                </div>
                <button className="btn btn-primary" onClick={() => startTest()} disabled={starting}>
                  {starting ? 'Starting...' : 'Start Custom Spike'}
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Live Metrics */}
      {metrics && (
        <>
          <div className="metrics-row" style={{ gridTemplateColumns: 'repeat(6, 1fr)' }}>
            <div className="metric-card">
              <div className="metric-value" style={{ color: isRunning ? 'var(--accent)' : 'var(--text-secondary)' }}>
                {metrics.qps}
              </div>
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

          {/* Charts side by side */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            <div className="card">
              <div className="card-header">
                <h3>Throughput (QPS)</h3>
                {history.length > 0 && (
                  <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                    peak: {Math.max(...history.map(h => h.qps)).toFixed(1)}
                  </span>
                )}
              </div>
              <div className="chart-area" style={{ minHeight: 160 }}>
                {history.length === 0 ? (
                  <div className="empty-state" style={{ padding: 16 }}><p>Waiting for data...</p></div>
                ) : (
                  history.map((h, i) => (
                    <div className="chart-bar-row" key={i} style={{ marginBottom: Math.max(1, 4 - Math.floor(history.length / 20)) }}>
                      <span className="chart-bar-label">{h.qps}</span>
                      <div className="chart-bar" style={{ width: `${(h.qps / maxQps) * 100}%`, height: barHeight }} />
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <h3>P95 Latency (ms)</h3>
                {history.length > 0 && (
                  <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                    peak: {Math.max(...history.map(h => h.p95)).toFixed(0)}ms
                  </span>
                )}
              </div>
              <div className="chart-area" style={{ minHeight: 160 }}>
                {history.length === 0 ? (
                  <div className="empty-state" style={{ padding: 16 }}><p>Waiting for data...</p></div>
                ) : (
                  history.map((h, i) => (
                    <div className="chart-bar-row" key={i} style={{ marginBottom: Math.max(1, 4 - Math.floor(history.length / 20)) }}>
                      <span className="chart-bar-label">{h.p95.toFixed(0)}</span>
                      <div className="chart-bar latency" style={{ width: `${(h.p95 / maxLat) * 100}%`, height: barHeight }} />
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Compute Timeline */}
          {computeHistory.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h3>Compute Activity Log</h3>
                <span className="badge badge-info">{computeHistory.length} samples</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {computeHistory.map((c, i) => (
                  <div key={i} className="compute-log-row">
                    <span className="compute-log-time">
                      {new Date(c.t).toLocaleTimeString()}
                    </span>
                    <span className={`badge ${c.state === 'ACTIVE' ? 'badge-success' : 'badge-warning'}`}>
                      {c.state}
                    </span>
                    <span className="compute-log-cu">
                      {c.min_cu}-{c.max_cu} CU
                    </span>
                    {i > 0 && computeHistory[i-1].state !== c.state && (
                      <span className="badge badge-info" style={{ marginLeft: 'auto' }}>STATE CHANGE</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
            <button className="btn btn-secondary btn-sm" onClick={() => api.clearLoadtestEvents()}>
              Clear Test Events from DB
            </button>
            <button className="btn btn-secondary btn-sm" onClick={() => { setHistory([]); setComputeHistory([]); setMetrics(null); setTestId(null) }}>
              Reset Charts
            </button>
          </div>
        </>
      )}

      {/* How it works */}
      {!metrics && (
        <div className="card">
          <h3 style={{ marginBottom: 12 }}>How Autoscaling Works</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: 13, lineHeight: 1.7, marginBottom: 16 }}>
            Lakebase autoscales compute between your configured <strong>min</strong> and <strong>max CU</strong> limits.
            When traffic increases, the autoscaler detects higher resource utilization and scales up compute
            to handle the load. When traffic subsides, compute scales back down. If there is zero activity,
            compute can scale to zero to minimize costs.
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
            <div style={{ padding: 14, background: 'var(--bg-primary)', borderRadius: 'var(--radius)', textAlign: 'center' }}>
              <div style={{ fontSize: 22, marginBottom: 6 }}>1</div>
              <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 4 }}>Send Spike</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Choose a preset or custom config</div>
            </div>
            <div style={{ padding: 14, background: 'var(--bg-primary)', borderRadius: 'var(--radius)', textAlign: 'center' }}>
              <div style={{ fontSize: 22, marginBottom: 6 }}>2</div>
              <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 4 }}>Watch QPS</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Traffic ramps up with workers</div>
            </div>
            <div style={{ padding: 14, background: 'var(--bg-primary)', borderRadius: 'var(--radius)', textAlign: 'center' }}>
              <div style={{ fontSize: 22, marginBottom: 6 }}>3</div>
              <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 4 }}>Observe Latency</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Initially rises, then stabilizes</div>
            </div>
            <div style={{ padding: 14, background: 'var(--bg-primary)', borderRadius: 'var(--radius)', textAlign: 'center' }}>
              <div style={{ fontSize: 22, marginBottom: 6 }}>4</div>
              <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 4 }}>Compute Scales</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Autoscaler adjusts CU allocation</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
